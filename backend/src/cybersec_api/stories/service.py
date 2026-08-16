from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersec_api.models.enrichment import Enrichment
from cybersec_api.models.item import Item
from cybersec_api.models.story import Story, StoryItem

EMBEDDING_DIMENSIONS = 384
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_.:-]{3,}")
SEVERITY_ORDER = {
    "informational": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}


@dataclass(slots=True)
class StoryCandidate:
    item: Item
    embedding: list[float]
    entities: set[str]
    keywords: list[str]
    risk_score: int
    severity: str | None
    seen_at: datetime | None


@dataclass(slots=True)
class StoryCluster:
    candidates: list[StoryCandidate] = field(default_factory=list)
    embedding: list[float] = field(default_factory=lambda: [0.0] * EMBEDDING_DIMENSIONS)
    entities: set[str] = field(default_factory=set)
    keywords: Counter[str] = field(default_factory=Counter)


@dataclass(slots=True)
class StorySyncResult:
    status: str
    candidates: int
    stories_created: int
    story_items_created: int
    stories_deleted: int
    skipped: int


def tokenize(value: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(value)]


def hash_token(token: str) -> tuple[int, float]:
    digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
    bucket = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return bucket, sign


def normalize_vector(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))

    if magnitude == 0:
        return vector

    return [round(value / magnitude, 8) for value in vector]


def embed_text(parts: list[str]) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS

    for part in parts:
        for token in tokenize(part):
            bucket, sign = hash_token(token)
            vector[bucket] += sign

    return normalize_vector(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=True)
    )


def entity_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0

    return len(left & right) / len(left | right)


def candidate_seen_at(item: Item) -> datetime | None:
    return item.published_at or item.collected_at or item.enriched_at


def candidate_text_parts(item: Item) -> list[str]:
    enrichment = item.enrichment
    cyber_entities = item.cyber_entities

    entity_values = [entity.normalized_value for entity in cyber_entities]
    ai_parts = []

    if enrichment is not None:
        ai_parts.extend(
            [
                enrichment.summary or "",
                " ".join(enrichment.tags or []),
                " ".join(enrichment.cves or []),
                " ".join(enrichment.iocs or []),
                " ".join(enrichment.mitre_attack or []),
            ]
        )

    return [
        item.normalized_title or item.title,
        item.normalized_content or item.summary or "",
        " ".join(entity_values),
        *ai_parts,
    ]


def candidate_keywords(item: Item) -> list[str]:
    preferred_types = {"cve", "ioc", "mitre_attack", "threat_actor"}
    cyber_entities = sorted(
        item.cyber_entities,
        key=lambda entity: (
            entity.entity_type not in preferred_types,
            -entity.risk_score,
            entity.normalized_value,
        ),
    )
    keywords = [entity.normalized_value for entity in cyber_entities[:8]]

    if not keywords and item.enrichment is not None:
        keywords = list(item.enrichment.tags or [])[:8]

    if not keywords:
        keywords = tokenize(item.normalized_title or item.title)[:8]

    return keywords


def candidate_entities(item: Item) -> set[str]:
    return {f"{entity.entity_type}:{entity.normalized_value}" for entity in item.cyber_entities}


def candidate_risk_score(item: Item) -> int:
    entity_scores = [entity.risk_score for entity in item.cyber_entities]

    if entity_scores:
        return max(entity_scores)

    confidence = item.enrichment.confidence if item.enrichment is not None else 50
    severity = item.enrichment.severity if item.enrichment is not None else "informational"
    return min(100, SEVERITY_ORDER.get(severity or "informational", 1) * 18 + confidence // 5)


def candidate_severity(item: Item) -> str | None:
    severities = [
        entity.severity for entity in item.cyber_entities if entity.severity is not None
    ]

    if item.enrichment is not None and item.enrichment.severity is not None:
        severities.append(item.enrichment.severity)

    if not severities:
        return None

    return max(severities, key=lambda severity: SEVERITY_ORDER.get(severity, 0))


def build_candidate(item: Item) -> StoryCandidate:
    return StoryCandidate(
        item=item,
        embedding=embed_text(candidate_text_parts(item)),
        entities=candidate_entities(item),
        keywords=candidate_keywords(item),
        risk_score=candidate_risk_score(item),
        severity=candidate_severity(item),
        seen_at=candidate_seen_at(item),
    )


def cluster_similarity(cluster: StoryCluster, candidate: StoryCandidate) -> float:
    vector_score = cosine_similarity(cluster.embedding, candidate.embedding)
    overlap_score = entity_overlap(cluster.entities, candidate.entities)
    return max(vector_score, overlap_score)


def refresh_cluster(cluster: StoryCluster) -> None:
    if not cluster.candidates:
        return

    embedding = [0.0] * EMBEDDING_DIMENSIONS
    entities: set[str] = set()
    keywords: Counter[str] = Counter()

    for candidate in cluster.candidates:
        for index, value in enumerate(candidate.embedding):
            embedding[index] += value
        entities.update(candidate.entities)
        keywords.update(candidate.keywords)

    count = len(cluster.candidates)
    cluster.embedding = normalize_vector([value / count for value in embedding])
    cluster.entities = entities
    cluster.keywords = keywords


def cluster_candidates(
    candidates: list[StoryCandidate],
    *,
    similarity_threshold: float,
) -> list[StoryCluster]:
    clusters: list[StoryCluster] = []

    for candidate in sorted(candidates, key=lambda item: item.risk_score, reverse=True):
        best_cluster: StoryCluster | None = None
        best_score = 0.0

        for cluster in clusters:
            score = cluster_similarity(cluster, candidate)
            if score > best_score:
                best_cluster = cluster
                best_score = score

        if best_cluster is not None and best_score >= similarity_threshold:
            best_cluster.candidates.append(candidate)
            refresh_cluster(best_cluster)
        else:
            cluster = StoryCluster(candidates=[candidate])
            refresh_cluster(cluster)
            clusters.append(cluster)

    return clusters


def story_fingerprint(cluster: StoryCluster) -> str:
    material = "|".join(sorted(cluster.entities)[:20])

    if not material:
        material = "|".join(keyword for keyword, _ in cluster.keywords.most_common(20))

    return hashlib.sha256(material.encode()).hexdigest()


def story_title(cluster: StoryCluster) -> str:
    keywords = [keyword for keyword, _ in cluster.keywords.most_common(3)]

    if keywords:
        return " / ".join(keywords)

    top_candidate = max(cluster.candidates, key=lambda candidate: candidate.risk_score)
    return top_candidate.item.normalized_title or top_candidate.item.title


def story_summary(cluster: StoryCluster) -> str | None:
    top_candidate = max(cluster.candidates, key=lambda candidate: candidate.risk_score)

    if top_candidate.item.enrichment is not None and top_candidate.item.enrichment.summary:
        return top_candidate.item.enrichment.summary

    return top_candidate.item.normalized_content or top_candidate.item.summary


def story_severity(cluster: StoryCluster) -> str | None:
    severities = [candidate.severity for candidate in cluster.candidates if candidate.severity]

    if not severities:
        return None

    return max(severities, key=lambda severity: SEVERITY_ORDER.get(severity, 0))


def story_first_seen(cluster: StoryCluster) -> datetime | None:
    values = [candidate.seen_at for candidate in cluster.candidates if candidate.seen_at]
    return min(values) if values else None


def story_last_seen(cluster: StoryCluster) -> datetime | None:
    values = [candidate.seen_at for candidate in cluster.candidates if candidate.seen_at]
    return max(values) if values else None


async def load_story_candidates(session: AsyncSession, *, limit: int) -> list[StoryCandidate]:
    statement = (
        select(Item)
        .join(Enrichment, Enrichment.item_id == Item.id)
        .options(
            selectinload(Item.source),
            selectinload(Item.enrichment),
            selectinload(Item.cyber_entities),
        )
        .where(Item.status == "normalized")
        .where(Item.is_duplicate.is_(False))
        .where(Enrichment.status == "completed")
        .order_by(Item.published_at.desc().nullslast(), Item.created_at.desc())
        .limit(limit)
    )
    items = list((await session.scalars(statement)).all())
    return [build_candidate(item) for item in items]


async def sync_stories(
    session: AsyncSession,
    *,
    limit: int = 500,
    similarity_threshold: float = 0.68,
) -> StorySyncResult:
    candidates = await load_story_candidates(session, limit=limit)
    story_items_deleted = await session.execute(delete(StoryItem))
    stories_deleted = await session.execute(delete(Story))
    clusters = cluster_candidates(candidates, similarity_threshold=similarity_threshold)

    story_items_created = 0

    for cluster in clusters:
        keywords = [keyword for keyword, _ in cluster.keywords.most_common(10)]
        story = Story(
            title=story_title(cluster),
            summary=story_summary(cluster),
            status="active",
            severity=story_severity(cluster),
            risk_score=max(candidate.risk_score for candidate in cluster.candidates),
            item_count=len(cluster.candidates),
            entity_count=len(cluster.entities),
            keywords=keywords,
            entity_fingerprint=story_fingerprint(cluster),
            embedding=cluster.embedding,
            first_seen_at=story_first_seen(cluster),
            last_seen_at=story_last_seen(cluster),
        )
        session.add(story)
        await session.flush()

        for candidate in cluster.candidates:
            relevance = round(cosine_similarity(story.embedding, candidate.embedding) * 100)
            story_item = StoryItem(
                story_id=story.id,
                item_id=candidate.item.id,
                relevance_score=max(1, min(relevance, 100)),
            )
            session.add(story_item)
            story_items_created += 1

    await session.commit()

    return StorySyncResult(
        status="ok",
        candidates=len(candidates),
        stories_created=len(clusters),
        story_items_created=story_items_created,
        stories_deleted=stories_deleted.rowcount or 0,
        skipped=max(0, (story_items_deleted.rowcount or 0) - story_items_created),
    )


def filtered_stories_statement(
    *,
    severity: str | None = None,
    min_score: int | None = None,
    search: str | None = None,
):
    statement = select(Story)

    if severity is not None:
        statement = statement.where(Story.severity == severity)

    if min_score is not None:
        statement = statement.where(Story.risk_score >= min_score)

    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Story.title.ilike(pattern),
                Story.summary.ilike(pattern),
                Story.entity_fingerprint.ilike(pattern),
            )
        )

    return statement


async def list_stories(
    session: AsyncSession,
    *,
    severity: str | None = None,
    min_score: int | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Story]:
    statement = filtered_stories_statement(
        severity=severity,
        min_score=min_score,
        search=search,
    ).order_by(Story.risk_score.desc(), Story.last_seen_at.desc().nullslast())
    return list((await session.scalars(statement.offset(offset).limit(limit))).all())


async def get_story(session: AsyncSession, story_id: UUID) -> Story | None:
    statement = (
        select(Story)
        .options(
            selectinload(Story.story_items)
            .selectinload(StoryItem.item)
            .selectinload(Item.source),
            selectinload(Story.story_items)
            .selectinload(StoryItem.item)
            .selectinload(Item.enrichment),
        )
        .where(Story.id == story_id)
    )
    return await session.scalar(statement)


async def count_stories(session: AsyncSession) -> int:
    return await session.scalar(select(func.count(Story.id))) or 0


async def count_high_risk_stories(session: AsyncSession) -> int:
    statement = select(func.count(Story.id)).where(Story.risk_score >= 70)
    return await session.scalar(statement) or 0


async def count_story_items(session: AsyncSession) -> int:
    return await session.scalar(select(func.count(StoryItem.item_id))) or 0
