from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.models.item import Item


async def list_items(
    session: AsyncSession,
    *,
    source_id: UUID | None = None,
    limit: int = 50,
) -> list[Item]:
    statement = select(Item).order_by(Item.published_at.desc().nullslast(), Item.created_at.desc())

    if source_id is not None:
        statement = statement.where(Item.source_id == source_id)

    result = await session.scalars(statement.limit(limit))
    return list(result.all())


async def get_item(session: AsyncSession, item_id: UUID) -> Item | None:
    return await session.get(Item, item_id)


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
