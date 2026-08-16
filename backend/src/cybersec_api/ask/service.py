from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersec_api.core.config import get_settings
from cybersec_api.models.enrichment import Enrichment
from cybersec_api.models.item import Item
from cybersec_api.models.story import StoryItem
from cybersec_api.schemas.ask import AskCitationRead, AskResponse
from cybersec_api.stories.service import cosine_similarity, embed_text, tokenize


class AskGenerationError(RuntimeError):
    pass


@dataclass(slots=True)
class AskCandidate:
    item: Item
    score: float
    excerpt: str
    entities: list[str]


def item_text_parts(item: Item) -> list[str]:
    enrichment = item.enrichment
    entities = " ".join(entity.normalized_value for entity in item.cyber_entities)

    return [
        item.normalized_title or item.title,
        item.normalized_content or item.summary or "",
        enrichment.summary if enrichment is not None and enrichment.summary else "",
        " ".join(enrichment.tags or []) if enrichment is not None else "",
        " ".join(enrichment.cves or []) if enrichment is not None else "",
        " ".join(enrichment.iocs or []) if enrichment is not None else "",
        " ".join(enrichment.mitre_attack or []) if enrichment is not None else "",
        entities,
    ]


def build_excerpt(item: Item, query_tokens: set[str], *, max_chars: int = 360) -> str:
    enrichment = item.enrichment
    candidates = [
        enrichment.summary if enrichment is not None else None,
        item.summary,
        item.normalized_content,
        item.raw_content,
    ]
    text = next((candidate for candidate in candidates if candidate), item.title)
    sentences = [sentence.strip() for sentence in text.replace("\n", " ").split(".")]
    best_sentence = max(
        sentences,
        key=lambda sentence: len(set(tokenize(sentence)) & query_tokens),
        default=text,
    )
    excerpt = best_sentence or text

    if len(excerpt) <= max_chars:
        return excerpt

    return f"{excerpt[: max_chars - 3].rstrip()}..."


def story_ids(item: Item) -> list:
    return [
        story_item.story_id
        for story_item in item.story_items
        if story_item.story_id is not None
    ]


def citation_from_candidate(index: int, candidate: AskCandidate) -> AskCitationRead:
    item = candidate.item
    return AskCitationRead(
        citation_id=f"S{index}",
        item_id=item.id,
        story_ids=story_ids(item),
        title=item.normalized_title or item.title,
        url=item.url,
        source_name=item.source_name,
        published_at=item.published_at,
        collected_at=item.collected_at,
        score=round(candidate.score, 3),
        excerpt=candidate.excerpt,
        entities=candidate.entities[:12],
    )


def score_item(
    item: Item,
    question: str,
    query_tokens: set[str],
    query_embedding: list[float],
) -> float:
    parts = item_text_parts(item)
    text = " ".join(parts)
    text_tokens = set(tokenize(text))
    token_score = len(text_tokens & query_tokens) / max(len(query_tokens), 1)
    vector_score = cosine_similarity(query_embedding, embed_text(parts))
    entity_boost = 0.0

    for entity in item.cyber_entities:
        if entity.normalized_value.lower() in question.lower():
            entity_boost += 0.18

    if item.enrichment is not None and item.enrichment.severity in {"high", "critical"}:
        entity_boost += 0.04

    return max(0.0, min(1.0, vector_score * 0.55 + token_score * 0.35 + entity_boost))


async def retrieve_citations(
    session: AsyncSession,
    *,
    question: str,
    limit: int,
) -> list[AskCitationRead]:
    query_tokens = set(tokenize(question))
    query_embedding = embed_text([question])
    statement = (
        select(Item)
        .join(Enrichment, Enrichment.item_id == Item.id)
        .options(
            selectinload(Item.source),
            selectinload(Item.enrichment),
            selectinload(Item.cyber_entities),
            selectinload(Item.story_items).selectinload(StoryItem.story),
        )
        .where(Item.status == "normalized")
        .where(Item.is_duplicate.is_(False))
        .where(Enrichment.status == "completed")
        .order_by(Item.published_at.desc().nullslast(), Item.collected_at.desc())
        .limit(350)
    )
    items = list((await session.scalars(statement)).unique().all())
    candidates: list[AskCandidate] = []

    for item in items:
        score = score_item(item, question, query_tokens, query_embedding)

        if score <= 0:
            continue

        entities = sorted(
            {entity.normalized_value for entity in item.cyber_entities},
            key=lambda value: (value.lower() not in question.lower(), value),
        )
        candidates.append(
            AskCandidate(
                item=item,
                score=score,
                excerpt=build_excerpt(item, query_tokens),
                entities=entities,
            )
        )

    ranked = sorted(
        candidates,
        key=lambda candidate: (
            candidate.score,
            candidate.item.published_at or candidate.item.collected_at,
        ),
        reverse=True,
    )[:limit]

    return [citation_from_candidate(index, candidate) for index, candidate in enumerate(ranked, 1)]


def citation_context(citations: list[AskCitationRead]) -> str:
    blocks = []

    for citation in citations:
        blocks.append(
            "\n".join(
                [
                    f"[{citation.citation_id}] {citation.title}",
                    f"Source: {citation.source_name or 'unknown'}",
                    f"URL: {citation.url}",
                    f"Entities: {', '.join(citation.entities) or 'none'}",
                    f"Excerpt: {citation.excerpt}",
                ]
            )
        )

    return "\n\n".join(blocks)


def local_answer(question: str, citations: list[AskCitationRead]) -> str:
    if not citations:
        return (
            "No encuentro evidencia suficiente en las noticias enriquecidas de CyberSec para "
            "responder con citas. Ejecuta Collect RSS, Normalize, Enrich Batch, Sync Intel y "
            "Sync Stories para ampliar el contexto disponible."
        )

    top = citations[0]
    supporting = citations[1:3]
    lines = [
        f"Respuesta basada en la evidencia disponible para: {question}",
        "",
        f"La senal principal es {top.title}. {top.excerpt} [{top.citation_id}]",
    ]

    if top.entities:
        lines.append(f"Entidades relacionadas: {', '.join(top.entities[:8])}.")

    if supporting:
        lines.append(
            "Tambien hay contexto relacionado en "
            + ", ".join(f"{citation.title} [{citation.citation_id}]" for citation in supporting)
            + "."
        )

    lines.append(
        "Trata esta respuesta como una sintesis operativa: revisa las citas antes de tomar "
        "decisiones defensivas."
    )
    return "\n".join(lines)


async def generate_ai_answer(question: str, citations: list[AskCitationRead]) -> str:
    settings = get_settings()
    api_key = settings.openrouter_api_key.get_secret_value() if settings.openrouter_api_key else ""

    if not api_key:
        raise AskGenerationError("OPENROUTER_API_KEY is not configured")

    prompt = "\n".join(
        [
            "Answer the analyst question using only the cited CyberSec evidence.",
            "Use concise Spanish unless the question is clearly in another language.",
            "Every factual claim must include citation markers like [S1] or [S2].",
            "If evidence is insufficient, say so and cite the closest evidence.",
            "",
            f"Question: {question}",
            "",
            "Evidence:",
            citation_context(citations),
        ]
    )
    request_body: dict[str, Any] = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": "You are Ask CyberSec, a careful CTI analyst. Never invent citations.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 700,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_app_url,
        "X-OpenRouter-Title": settings.openrouter_app_title,
    }

    async with httpx.AsyncClient(timeout=settings.openrouter_request_timeout_seconds) as client:
        response = await client.post(
            f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
            json=request_body,
            headers=headers,
        )
        response.raise_for_status()
        raw_response = response.json()

    try:
        answer = raw_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AskGenerationError("OpenRouter response did not contain answer content") from exc

    if not isinstance(answer, str) or not answer.strip():
        raise AskGenerationError("OpenRouter answer was empty")

    return answer.strip()


def follow_up_questions(citations: list[AskCitationRead]) -> list[str]:
    entity_values = []

    for citation in citations:
        entity_values.extend(citation.entities[:3])

    unique_entities = list(dict.fromkeys(entity_values))

    if unique_entities:
        return [
            f"Que noticias explican mejor {unique_entities[0]}?",
            "Cuales son las acciones defensivas recomendadas?",
            "Que historias conectan con esta entidad?",
        ]

    return [
        "Que noticias recientes tienen mayor riesgo?",
        "Que fuentes aportan mas contexto?",
        "Que entidades deberia priorizar?",
    ]


async def ask_cybersec(
    session: AsyncSession,
    *,
    question: str,
    limit: int,
    use_ai: bool,
) -> AskResponse:
    citations = await retrieve_citations(session, question=question, limit=limit)
    mode = "local"

    if use_ai and citations:
        try:
            answer = await generate_ai_answer(question, citations)
            mode = "openrouter"
        except Exception:
            answer = local_answer(question, citations)
            mode = "local_fallback"
    else:
        answer = local_answer(question, citations)

    confidence = min(95, 35 + len(citations) * 10 + round(sum(c.score for c in citations) * 10))

    return AskResponse(
        answer=answer,
        mode=mode,
        confidence=confidence if citations else 20,
        citations=citations,
        follow_up_questions=follow_up_questions(citations),
    )
