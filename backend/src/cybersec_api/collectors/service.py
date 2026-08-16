from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.collectors.rss import CollectionStats, collect_source
from cybersec_api.models.source import Source


async def collect_enabled_sources(session: AsyncSession) -> list[CollectionStats]:
    result = await session.scalars(
        select(Source)
        .where(Source.is_enabled.is_(True))
        .where(Source.source_type == "rss")
        .order_by(Source.name.asc())
    )
    sources = list(result.all())
    stats: list[CollectionStats] = []

    for source in sources:
        stats.append(await collect_source(session, source))

    return stats
