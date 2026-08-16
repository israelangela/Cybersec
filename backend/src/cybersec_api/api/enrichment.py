from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.db.session import get_session
from cybersec_api.enrichment.openrouter import OpenRouterConfigurationError
from cybersec_api.enrichment.service import (
    enrich_item,
    enrich_pending_items,
    get_enrichable_item,
    get_enrichment,
)
from cybersec_api.schemas.enrichment import (
    EnrichmentRead,
    EnrichmentRunResultRead,
    ItemEnrichmentResultRead,
)

router = APIRouter(prefix="/enrichment", tags=["enrichment"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
EnrichmentLimit = Annotated[int, Query(ge=1, le=50)]


@router.get("/items/{item_id}", response_model=EnrichmentRead)
async def read_item_enrichment(item_id: UUID, session: DatabaseSession) -> EnrichmentRead:
    enrichment = await get_enrichment(session, item_id)

    if enrichment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrichment not found")

    return enrichment


@router.post("/items/{item_id}/run", response_model=ItemEnrichmentResultRead)
async def run_item_enrichment(
    item_id: UUID,
    session: DatabaseSession,
) -> ItemEnrichmentResultRead:
    item = await get_enrichable_item(session, item_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    try:
        result = await enrich_item(session, item)
    except OpenRouterConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    await session.commit()
    return ItemEnrichmentResultRead(**asdict(result))


@router.post("/run", response_model=EnrichmentRunResultRead)
async def run_enrichment(
    session: DatabaseSession,
    limit: EnrichmentLimit = 10,
) -> EnrichmentRunResultRead:
    try:
        return await enrich_pending_items(session, limit=limit)
    except OpenRouterConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
