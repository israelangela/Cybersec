import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from cybersec_api.collectors.service import collect_enabled_sources
from cybersec_api.core.config import Settings
from cybersec_api.db.session import SessionLocal

logger = structlog.get_logger(__name__)


async def scheduled_collect_sources() -> None:
    async with SessionLocal() as session:
        results = await collect_enabled_sources(session)
        logger.info(
            "collection_job_finished",
            sources_checked=len(results),
            created=sum(result.created for result in results),
            duplicates=sum(result.duplicates for result in results),
            errors=sum(1 for result in results if result.status == "error"),
        )


def build_scheduler(settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_collect_sources,
        trigger="interval",
        minutes=settings.collector_interval_minutes,
        id="collect_sources",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
