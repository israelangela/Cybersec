from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersec_api.models.item import Item
from cybersec_api.models.source import Source


def filtered_items_statement(
    *,
    source_id: UUID | None = None,
    status: str | None = None,
    language: str | None = None,
    is_duplicate: bool | None = None,
    search: str | None = None,
):
    statement = select(Item).options(selectinload(Item.source))

    if source_id is not None:
        statement = statement.where(Item.source_id == source_id)

    if status is not None:
        statement = statement.where(Item.status == status)

    if language is not None:
        statement = statement.where(Item.language == language)

    if is_duplicate is not None:
        statement = statement.where(Item.is_duplicate.is_(is_duplicate))

    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Item.title.ilike(pattern),
                Item.url.ilike(pattern),
                Item.summary.ilike(pattern),
                Item.raw_content.ilike(pattern),
                Item.normalized_title.ilike(pattern),
                Item.normalized_content.ilike(pattern),
            )
        )

    return statement

async def list_items(
    session: AsyncSession,
    *,
    source_id: UUID | None = None,
    status: str | None = None,
    language: str | None = None,
    is_duplicate: bool | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Item]:
    statement = filtered_items_statement(
        source_id=source_id,
        status=status,
        language=language,
        is_duplicate=is_duplicate,
        search=search,
    ).order_by(Item.published_at.desc().nullslast(), Item.created_at.desc())

    result = await session.scalars(statement.offset(offset).limit(limit))
    return list(result.all())


async def get_item(session: AsyncSession, item_id: UUID) -> Item | None:
    statement = select(Item).options(selectinload(Item.source)).where(Item.id == item_id)
    return await session.scalar(statement)


async def count_items(
    session: AsyncSession,
    *,
    status: str | None = None,
    is_duplicate: bool | None = None,
) -> int:
    statement = select(func.count(Item.id))

    if status is not None:
        statement = statement.where(Item.status == status)

    if is_duplicate is not None:
        statement = statement.where(Item.is_duplicate.is_(is_duplicate))

    return await session.scalar(statement) or 0


async def count_items_by_language(session: AsyncSession) -> list[tuple[str, int]]:
    language_expression = func.coalesce(Item.language, "unknown")
    statement = (
        select(language_expression, func.count(Item.id))
        .group_by(language_expression)
        .order_by(func.count(Item.id).desc())
    )
    return [(language, count) for language, count in (await session.execute(statement)).all()]


async def count_items_by_source(session: AsyncSession) -> list[tuple[UUID, str, int, object]]:
    statement = (
        select(Source.id, Source.name, func.count(Item.id), func.max(Item.collected_at))
        .join(Item, Item.source_id == Source.id)
        .group_by(Source.id, Source.name)
        .order_by(func.count(Item.id).desc(), Source.name.asc())
    )
    return list((await session.execute(statement)).all())


async def item_exists(
    session: AsyncSession,
    *,
    source_id: UUID,
    url: str,
    content_hash: str,
    external_id: str | None,
) -> bool:
    conditions = [Item.url == url, Item.content_hash == content_hash]

    if external_id:
        conditions.append((Item.source_id == source_id) & (Item.external_id == external_id))

    statement = select(Item.id).where(or_(*conditions)).limit(1)
    existing = await session.scalar(statement)
    return existing is not None
