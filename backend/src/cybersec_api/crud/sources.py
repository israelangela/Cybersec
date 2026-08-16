from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.models.source import Source
from cybersec_api.schemas.source import SourceCreate, SourceUpdate


async def list_sources(
    session: AsyncSession,
    *,
    is_enabled: bool | None = None,
    source_type: str | None = None,
) -> list[Source]:
    statement = select(Source).order_by(Source.name.asc())

    if is_enabled is not None:
        statement = statement.where(Source.is_enabled.is_(is_enabled))

    if source_type is not None:
        statement = statement.where(Source.source_type == source_type)

    result = await session.scalars(statement)
    return list(result.all())


async def get_source(session: AsyncSession, source_id: UUID) -> Source | None:
    return await session.get(Source, source_id)


async def create_source(session: AsyncSession, payload: SourceCreate) -> Source:
    source = Source(**payload.model_dump(mode="json"))
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


async def update_source(session: AsyncSession, source: Source, payload: SourceUpdate) -> Source:
    update_data = payload.model_dump(exclude_unset=True, mode="json")

    for field, value in update_data.items():
        setattr(source, field, value)

    await session.commit()
    await session.refresh(source)
    return source


async def delete_source(session: AsyncSession, source: Source) -> None:
    await session.delete(source)
    await session.commit()
