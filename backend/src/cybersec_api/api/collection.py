from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.collectors.rss import collect_source
from cybersec_api.collectors.service import collect_enabled_sources
from cybersec_api.crud.sources import get_source
from cybersec_api.db.session import get_session
from cybersec_api.schemas.collection import CollectionRunResult, SourceCollectionResult

router = APIRouter(prefix="/collection", tags=["collection"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


def summarize_results(results: list[SourceCollectionResult]) -> CollectionRunResult:
    return CollectionRunResult(
        status="ok" if all(result.status != "error" for result in results) else "partial",
        sources_checked=len(results),
        fetched=sum(result.fetched for result in results),
        created=sum(result.created for result in results),
        duplicates=sum(result.duplicates for result in results),
        skipped=sum(result.skipped for result in results),
        errors=sum(1 for result in results if result.status == "error"),
        results=results,
    )


@router.post("/run", response_model=CollectionRunResult)
async def run_collection(session: DatabaseSession) -> CollectionRunResult:
    stats = await collect_enabled_sources(session)
    results = [SourceCollectionResult.model_validate(stat, from_attributes=True) for stat in stats]
    return summarize_results(results)


@router.post("/sources/{source_id}/run", response_model=SourceCollectionResult)
async def run_source_collection(
    source_id: UUID,
    session: DatabaseSession,
) -> SourceCollectionResult:
    source = await get_source(session, source_id)

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    stats = await collect_source(session, source)
    return SourceCollectionResult.model_validate(stats, from_attributes=True)
