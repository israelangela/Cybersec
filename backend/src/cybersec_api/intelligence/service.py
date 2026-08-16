from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersec_api.models.cyber_entity import CyberEntity
from cybersec_api.models.enrichment import Enrichment
from cybersec_api.models.item import Item
from cybersec_api.models.story import Story, StoryItem

SEVERITY_ORDER = {
    "informational": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}
SEVERITY_SCORE = {
    "informational": 10,
    "low": 25,
    "medium": 50,
    "high": 75,
    "critical": 95,
}
ENTITY_TYPE_BONUS = {
    "tag": 0,
    "ioc": 5,
    "cve": 8,
    "mitre_attack": 6,
    "threat_actor": 12,
}
MITRE_PATTERN = re.compile(r"\bT\d{4}(?:\.\d{3})?\b", re.IGNORECASE)
THREAT_ACTOR_PATTERN = re.compile(r"\b(?:APT|TA|UNC|FIN)\d{1,5}\b", re.IGNORECASE)


@dataclass(slots=True)
class ExtractedEntity:
    entity_type: str
    value: str
    normalized_value: str
    evidence_field: str


@dataclass(slots=True)
class IntelligenceSyncResult:
    status: str
    enrichments_checked: int
    entities_created: int
    entities_deleted: int
    skipped: int


EntityAggregateRow = tuple[
    str,
    str,
    str,
    int,
    int,
    float | None,
    str | None,
    datetime | None,
    datetime | None,
]


def clean_value(value: object) -> str:
    return str(value).strip()


def normalize_entity(entity_type: str, value: str) -> str:
    cleaned = " ".join(value.split())

    if entity_type == "cve":
        return cleaned.upper()

    if entity_type == "mitre_attack":
        match = MITRE_PATTERN.search(cleaned)
        return match.group(0).upper() if match else cleaned.upper()

    if entity_type == "threat_actor":
        return cleaned.upper()

    return cleaned.lower()


def add_entity(
    entities: dict[tuple[str, str], ExtractedEntity],
    *,
    entity_type: str,
    value: object,
    evidence_field: str,
) -> None:
    cleaned = clean_value(value)

    if not cleaned:
        return

    normalized = normalize_entity(entity_type, cleaned)
    entities[(entity_type, normalized)] = ExtractedEntity(
        entity_type=entity_type,
        value=cleaned,
        normalized_value=normalized,
        evidence_field=evidence_field,
    )


def extract_threat_actors(enrichment: Enrichment) -> list[str]:
    text_parts = [
        enrichment.summary or "",
        " ".join(enrichment.tags or []),
        " ".join(enrichment.recommended_actions or []),
    ]
    combined = " ".join(text_parts)
    return sorted({match.group(0).upper() for match in THREAT_ACTOR_PATTERN.finditer(combined)})


def extract_entities(enrichment: Enrichment) -> list[ExtractedEntity]:
    entities: dict[tuple[str, str], ExtractedEntity] = {}

    for value in enrichment.cves or []:
        add_entity(entities, entity_type="cve", value=value, evidence_field="cves")

    for value in enrichment.iocs or []:
        add_entity(entities, entity_type="ioc", value=value, evidence_field="iocs")

    for value in enrichment.mitre_attack or []:
        if MITRE_PATTERN.search(clean_value(value)):
            add_entity(
                entities,
                entity_type="mitre_attack",
                value=value,
                evidence_field="mitre_attack",
            )

    for value in enrichment.tags or []:
        add_entity(entities, entity_type="tag", value=value, evidence_field="tags")

    for value in extract_threat_actors(enrichment):
        add_entity(
            entities,
            entity_type="threat_actor",
            value=value,
            evidence_field="summary",
        )

    return list(entities.values())


def calculate_risk_score(entity_type: str, severity: str | None, confidence: int | None) -> int:
    base_score = SEVERITY_SCORE.get(severity or "informational", 10)
    confidence_value = max(0, min(confidence if confidence is not None else 50, 100))
    confidence_factor = 0.5 + (confidence_value / 200)
    score = round(base_score * confidence_factor) + ENTITY_TYPE_BONUS.get(entity_type, 0)
    return max(1, min(score, 100))


def entity_seen_at(enrichment: Enrichment) -> datetime | None:
    item = enrichment.item
    return item.published_at or item.collected_at or enrichment.enriched_at


async def sync_intelligence_entities(
    session: AsyncSession,
    *,
    limit: int = 500,
) -> IntelligenceSyncResult:
    statement = (
        select(Enrichment)
        .options(selectinload(Enrichment.item))
        .where(Enrichment.status == "completed")
        .order_by(Enrichment.enriched_at.desc().nullslast(), Enrichment.created_at.desc())
        .limit(limit)
    )
    enrichments = list((await session.scalars(statement)).all())
    entities_created = 0
    entities_deleted = 0
    skipped = 0

    for enrichment in enrichments:
        if enrichment.item is None:
            skipped += 1
            continue

        delete_statement = delete(CyberEntity).where(CyberEntity.item_id == enrichment.item_id)
        delete_result = await session.execute(delete_statement)
        entities_deleted += delete_result.rowcount or 0

        seen_at = entity_seen_at(enrichment)
        extracted_entities = extract_entities(enrichment)

        if not extracted_entities:
            skipped += 1
            continue

        for extracted in extracted_entities:
            entity = CyberEntity(
                item_id=enrichment.item_id,
                enrichment_id=enrichment.id,
                entity_type=extracted.entity_type,
                value=extracted.value,
                normalized_value=extracted.normalized_value,
                severity=enrichment.severity,
                confidence=enrichment.confidence,
                risk_score=calculate_risk_score(
                    extracted.entity_type,
                    enrichment.severity,
                    enrichment.confidence,
                ),
                evidence={
                    "field": extracted.evidence_field,
                    "item_title": enrichment.item.normalized_title or enrichment.item.title,
                    "source_url": enrichment.item.url,
                    "summary": enrichment.summary,
                },
                first_seen_at=seen_at,
                last_seen_at=seen_at,
            )
            session.add(entity)
            entities_created += 1

    await session.commit()

    return IntelligenceSyncResult(
        status="ok",
        enrichments_checked=len(enrichments),
        entities_created=entities_created,
        entities_deleted=entities_deleted,
        skipped=skipped,
    )


def filtered_entities_statement(
    *,
    entity_type: str | None = None,
    severity: str | None = None,
    min_score: int | None = None,
    search: str | None = None,
):
    statement = select(CyberEntity)

    if entity_type is not None:
        statement = statement.where(CyberEntity.entity_type == entity_type)

    if severity is not None:
        statement = statement.where(CyberEntity.severity == severity)

    if min_score is not None:
        statement = statement.where(CyberEntity.risk_score >= min_score)

    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                CyberEntity.value.ilike(pattern),
                CyberEntity.normalized_value.ilike(pattern),
                CyberEntity.entity_type.ilike(pattern),
            )
        )

    return statement


async def list_item_entities(session: AsyncSession, item_id: UUID) -> list[CyberEntity]:
    statement = (
        select(CyberEntity)
        .where(CyberEntity.item_id == item_id)
        .order_by(CyberEntity.risk_score.desc(), CyberEntity.entity_type.asc())
    )
    return list((await session.scalars(statement)).all())


async def list_entity_aggregates(
    session: AsyncSession,
    *,
    entity_type: str | None = None,
    severity: str | None = None,
    min_score: int | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[EntityAggregateRow]:
    filtered = filtered_entities_statement(
        entity_type=entity_type,
        severity=severity,
        min_score=min_score,
        search=search,
    ).subquery()

    statement = (
        select(
            filtered.c.entity_type,
            func.min(filtered.c.value),
            filtered.c.normalized_value,
            func.count(filtered.c.id),
            func.max(filtered.c.risk_score),
            func.avg(filtered.c.confidence),
            func.max(filtered.c.severity),
            func.min(filtered.c.first_seen_at),
            func.max(filtered.c.last_seen_at),
        )
        .group_by(filtered.c.entity_type, filtered.c.normalized_value)
        .order_by(func.max(filtered.c.risk_score).desc(), func.count(filtered.c.id).desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await session.execute(statement)).all())


async def count_total_entities(session: AsyncSession) -> int:
    return await session.scalar(select(func.count(CyberEntity.id))) or 0


async def count_unique_entities(session: AsyncSession) -> int:
    distinct_entities = (
        select(CyberEntity.entity_type, CyberEntity.normalized_value).distinct().subquery()
    )
    return await session.scalar(select(func.count()).select_from(distinct_entities)) or 0


async def count_high_risk_entities(session: AsyncSession) -> int:
    statement = select(func.count(CyberEntity.id)).where(CyberEntity.risk_score >= 70)
    return await session.scalar(statement) or 0


async def count_entities_by_type(session: AsyncSession) -> list[tuple[str, int]]:
    statement = (
        select(CyberEntity.entity_type, func.count(CyberEntity.id))
        .group_by(CyberEntity.entity_type)
        .order_by(func.count(CyberEntity.id).desc(), CyberEntity.entity_type.asc())
    )
    return list((await session.execute(statement)).all())


async def list_top_risk_entities(session: AsyncSession, limit: int = 10) -> list[CyberEntity]:
    statement = (
        select(CyberEntity)
        .order_by(CyberEntity.risk_score.desc(), CyberEntity.last_seen_at.desc().nullslast())
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


def external_references(entity_type: str, normalized_value: str) -> list[tuple[str, str]]:
    if entity_type == "cve" and normalized_value.upper().startswith("CVE-"):
        cve = normalized_value.upper()
        return [
            ("NVD", f"https://nvd.nist.gov/vuln/detail/{cve}"),
            ("CVE.org", f"https://www.cve.org/CVERecord?id={cve}"),
        ]

    if entity_type == "mitre_attack" and MITRE_PATTERN.fullmatch(normalized_value.upper()):
        technique_path = normalized_value.upper().replace(".", "/")
        return [("MITRE ATT&CK", f"https://attack.mitre.org/techniques/{technique_path}/")]

    return []


async def list_entity_items(
    session: AsyncSession,
    *,
    entity_type: str,
    normalized_value: str,
    limit: int = 100,
) -> list[Item]:
    normalized = normalize_entity(entity_type, normalized_value)
    statement = (
        select(Item)
        .join(CyberEntity, CyberEntity.item_id == Item.id)
        .options(selectinload(Item.source), selectinload(Item.enrichment))
        .where(CyberEntity.entity_type == entity_type)
        .where(CyberEntity.normalized_value == normalized)
        .order_by(Item.published_at.desc().nullslast(), Item.collected_at.desc())
        .limit(limit)
    )
    return list((await session.scalars(statement)).unique().all())


async def list_entity_stories(
    session: AsyncSession,
    *,
    entity_type: str,
    normalized_value: str,
    limit: int = 50,
) -> list[Story]:
    normalized = normalize_entity(entity_type, normalized_value)
    statement = (
        select(Story)
        .join(StoryItem, StoryItem.story_id == Story.id)
        .join(CyberEntity, CyberEntity.item_id == StoryItem.item_id)
        .where(CyberEntity.entity_type == entity_type)
        .where(CyberEntity.normalized_value == normalized)
        .order_by(Story.risk_score.desc(), Story.last_seen_at.desc().nullslast())
        .limit(limit)
    )
    return list((await session.scalars(statement)).unique().all())


async def list_item_stories(session: AsyncSession, item_id: UUID) -> list[Story]:
    statement = (
        select(Story)
        .join(StoryItem, StoryItem.story_id == Story.id)
        .where(StoryItem.item_id == item_id)
        .order_by(Story.risk_score.desc(), Story.last_seen_at.desc().nullslast())
    )
    return list((await session.scalars(statement)).all())
