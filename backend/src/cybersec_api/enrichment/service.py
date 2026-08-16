from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersec_api.core.config import get_settings
from cybersec_api.enrichment.openrouter import OpenRouterConfigurationError, enrich_with_openrouter
from cybersec_api.models.enrichment import Enrichment
from cybersec_api.models.item import Item
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


class EnrichmentProvider(Protocol):
    async def __call__(
        self,
        *,
        title: str,
        content: str,
        source_name: str | None,
        url: str,
    ) -> tuple[AIEnrichmentPayload, dict]:
        pass


@dataclass(slots=True)
class ItemEnrichmentResult:
    item_id: UUID
    status: str
    enrichment: Enrichment | None = None
    error: str | None = None


@dataclass(slots=True)
class EnrichmentRunResult:
    status: str
    candidates: int
    enriched: int
    failed: int
    skipped: int
    results: list[ItemEnrichmentResult]


async def openrouter_provider(
    *,
    title: str,
    content: str,
    source_name: str | None,
    url: str,
) -> tuple[AIEnrichmentPayload, dict]:
    return await enrich_with_openrouter(
        settings=get_settings(),
        title=title,
        content=content,
        source_name=source_name,
        url=url,
    )


async def get_enrichment(session: AsyncSession, item_id: UUID) -> Enrichment | None:
    statement = select(Enrichment).where(Enrichment.item_id == item_id)
    return await session.scalar(statement)


async def get_enrichable_item(session: AsyncSession, item_id: UUID) -> Item | None:
    statement = (
        select(Item)
        .options(selectinload(Item.source), selectinload(Item.enrichment))
        .where(Item.id == item_id)
    )
    return await session.scalar(statement)


def item_content(item: Item) -> tuple[str, str]:
    title = item.normalized_title or item.title
    content = item.normalized_content or item.summary or item.raw_content or item.title
    return title, content


def empty_failed_enrichment(item: Item, error: str) -> Enrichment:
    return Enrichment(
        item_id=item.id,
        provider="openrouter",
        model=get_settings().openrouter_model,
        status="error",
        summary=None,
        severity=None,
        confidence=None,
        tags=[],
        cves=[],
        iocs=[],
        mitre_attack=[],
        recommended_actions=[],
        raw_response={},
        error=error,
        enriched_at=datetime.now(UTC),
    )


async def upsert_enrichment(
    session: AsyncSession,
    item: Item,
    payload: AIEnrichmentPayload,
    raw_response: dict,
) -> Enrichment:
    existing = (
        item.enrichment
        if item.enrichment is not None
        else await get_enrichment(session, item.id)
    )
    enrichment = existing if existing is not None else Enrichment(item_id=item.id)

    enrichment.provider = "openrouter"
    enrichment.model = get_settings().openrouter_model
    enrichment.status = "completed"
    enrichment.summary = payload.summary
    enrichment.severity = payload.severity
    enrichment.confidence = payload.confidence
    enrichment.tags = payload.tags
    enrichment.cves = payload.cves
    enrichment.iocs = payload.iocs
    enrichment.mitre_attack = payload.mitre_attack
    enrichment.recommended_actions = payload.recommended_actions
    enrichment.raw_response = raw_response
    enrichment.error = None
    enrichment.enriched_at = datetime.now(UTC)

    if existing is None:
        session.add(enrichment)

    return enrichment


async def mark_enrichment_error(session: AsyncSession, item: Item, error: str) -> Enrichment:
    existing = (
        item.enrichment
        if item.enrichment is not None
        else await get_enrichment(session, item.id)
    )
    enrichment = existing if existing is not None else empty_failed_enrichment(item, error)

    enrichment.provider = "openrouter"
    enrichment.model = get_settings().openrouter_model
    enrichment.status = "error"
    enrichment.summary = None
    enrichment.severity = None
    enrichment.confidence = None
    enrichment.tags = []
    enrichment.cves = []
    enrichment.iocs = []
    enrichment.mitre_attack = []
    enrichment.recommended_actions = []
    enrichment.raw_response = {}
    enrichment.error = error
    enrichment.enriched_at = datetime.now(UTC)

    if existing is None:
        session.add(enrichment)

    return enrichment


async def enrich_item(
    session: AsyncSession,
    item: Item,
    *,
    provider: EnrichmentProvider = openrouter_provider,
) -> ItemEnrichmentResult:
    if item.status != "normalized":
        return ItemEnrichmentResult(
            item_id=item.id,
            status="skipped",
            error="Only normalized, non-duplicate items can be enriched",
        )

    if item.is_duplicate:
        return ItemEnrichmentResult(
            item_id=item.id,
            status="skipped",
            error="Duplicate items are not enriched in Phase 5",
        )

    title, content = item_content(item)

    try:
        payload, raw_response = await provider(
            title=title,
            content=content,
            source_name=item.source_name,
            url=item.url,
        )
        enrichment = await upsert_enrichment(session, item, payload, raw_response)
        await session.flush()
        await session.refresh(enrichment)
        return ItemEnrichmentResult(item_id=item.id, status="completed", enrichment=enrichment)
    except OpenRouterConfigurationError:
        raise
    except Exception as exc:
        enrichment = await mark_enrichment_error(session, item, str(exc))
        await session.flush()
        await session.refresh(enrichment)
        return ItemEnrichmentResult(
            item_id=item.id,
            status="error",
            enrichment=enrichment,
            error=str(exc),
        )


async def enrich_pending_items(
    session: AsyncSession,
    *,
    limit: int = 10,
    provider: EnrichmentProvider = openrouter_provider,
) -> EnrichmentRunResult:
    statement = (
        select(Item)
        .options(selectinload(Item.source), selectinload(Item.enrichment))
        .outerjoin(Enrichment, Enrichment.item_id == Item.id)
        .where(Item.status == "normalized")
        .where(Item.is_duplicate.is_(False))
        .where(Enrichment.id.is_(None))
        .order_by(Item.published_at.desc().nullslast(), Item.created_at.desc())
        .limit(limit)
    )
    items = list((await session.scalars(statement)).all())
    results: list[ItemEnrichmentResult] = []

    for item in items:
        results.append(await enrich_item(session, item, provider=provider))

    await session.commit()

    enriched = sum(1 for result in results if result.status == "completed")
    failed = sum(1 for result in results if result.status == "error")
    skipped = sum(1 for result in results if result.status == "skipped")

    return EnrichmentRunResult(
        status="ok" if failed == 0 else "partial",
        candidates=len(items),
        enriched=enriched,
        failed=failed,
        skipped=skipped,
        results=results,
    )
