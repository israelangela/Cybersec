from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.models.enrichment import Enrichment


async def count_enrichments(session: AsyncSession, *, status: str | None = None) -> int:
    statement = select(func.count(Enrichment.id))

    if status is not None:
        statement = statement.where(Enrichment.status == status)

    return await session.scalar(statement) or 0
