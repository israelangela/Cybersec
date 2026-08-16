from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.crud.items import get_item, list_items
from cybersec_api.db.session import get_session
from cybersec_api.schemas.item import ItemRead

router = APIRouter(prefix="/items", tags=["items"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
ItemLimit = Annotated[int, Query(ge=1, le=200)]


@router.get("", response_model=list[ItemRead])
async def read_items(
    session: DatabaseSession,
    source_id: UUID | None = None,
    limit: ItemLimit = 50,
) -> list[ItemRead]:
    return await list_items(session, source_id=source_id, limit=limit)


@router.get("/{item_id}", response_model=ItemRead)
async def read_item(item_id: UUID, session: DatabaseSession) -> ItemRead:
    item = await get_item(session, item_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return item
