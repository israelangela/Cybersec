from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.models.item import Item
from cybersec_api.normalizers.text import detect_language, normalized_hash, normalize_content


@dataclass(slots=True)
class ItemNormalizationResult:
    item_id: UUID
    status: str
    language: str | None = None
    normalized_hash: str | None = None
    duplicate_of_item_id: UUID | None = None
    error: str | None = None


@dataclass(slots=True)
class NormalizationRunResult:
    status: str
    candidates: int
    normalized: int
    duplicates: int
    failed: int
    skipped: int
    results: list[ItemNormalizationResult]


async def find_original_item(
    session: AsyncSession,
    *,
    item_id: UUID,
    item_hash: str,
) -> Item | None:
    statement = (
        select(Item)
        .where(Item.id != item_id)
        .where(Item.normalized_hash == item_hash)
        .where(Item.is_duplicate.is_(False))
        .order_by(Item.created_at.asc())
        .limit(1)
    )
    return await session.scalar(statement)


async def normalize_item(session: AsyncSession, item: Item) -> ItemNormalizationResult:
    try:
        title = normalize_content(item.title) or "Untitled intelligence item"
        content = normalize_content(item.raw_content or item.summary or item.title)
        item_hash = normalized_hash(title, content)
        duplicate = await find_original_item(session, item_id=item.id, item_hash=item_hash)

        item.normalized_title = title
        item.normalized_content = content
        item.normalized_hash = item_hash
        item.language = detect_language(title, content)
        item.normalized_at = datetime.now(UTC)
        item.normalization_error = None

        if duplicate is not None:
            item.status = "duplicate"
            item.is_duplicate = True
            item.duplicate_of_item_id = duplicate.id
        else:
            item.status = "normalized"
            item.is_duplicate = False
            item.duplicate_of_item_id = None

        return ItemNormalizationResult(
            item_id=item.id,
            status=item.status,
            language=item.language,
            normalized_hash=item.normalized_hash,
            duplicate_of_item_id=item.duplicate_of_item_id,
        )
    except Exception as exc:
        item.status = "normalization_error"
        item.normalization_error = str(exc)
        item.normalized_at = datetime.now(UTC)
        return ItemNormalizationResult(item_id=item.id, status=item.status, error=str(exc))


async def normalize_pending_items(session: AsyncSession, *, limit: int = 100) -> NormalizationRunResult:
    statement = (
        select(Item)
        .where(Item.status.in_(["raw", "normalization_error"]))
        .order_by(Item.collected_at.asc())
        .limit(limit)
    )
    items = list((await session.scalars(statement)).all())
    results: list[ItemNormalizationResult] = []

    for item in items:
        results.append(await normalize_item(session, item))
        await session.flush()

    await session.commit()

    failed = sum(1 for result in results if result.status == "normalization_error")
    duplicates = sum(1 for result in results if result.status == "duplicate")
    normalized = sum(1 for result in results if result.status == "normalized")

    return NormalizationRunResult(
        status="ok" if failed == 0 else "partial",
        candidates=len(items),
        normalized=normalized,
        duplicates=duplicates,
        failed=failed,
        skipped=0,
        results=results,
    )
