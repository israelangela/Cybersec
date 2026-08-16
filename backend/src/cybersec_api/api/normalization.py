from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.crud.items import get_item
from cybersec_api.db.session import get_session
from cybersec_api.normalizers.service import normalize_item, normalize_pending_items
from cybersec_api.schemas.normalization import (
    ItemNormalizationRead,
    NormalizationRunResultRead,
)

router = APIRouter(prefix="/normalization", tags=["normalization"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
NormalizationLimit = Annotated[int, Query(ge=1, le=500)]


@router.post("/run", response_model=NormalizationRunResultRead)
async def run_normalization(
    session: DatabaseSession,
    limit: NormalizationLimit = 100,
) -> NormalizationRunResultRead:
    return await normalize_pending_items(session, limit=limit)


@router.post("/items/{item_id}/run", response_model=ItemNormalizationRead)
async def run_item_normalization(
    item_id: UUID,
    session: DatabaseSession,
) -> ItemNormalizationRead:
    item = await get_item(session, item_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    result = await normalize_item(session, item)
    await session.commit()
    return ItemNormalizationRead(**asdict(result), normalized_at=item.normalized_at)
