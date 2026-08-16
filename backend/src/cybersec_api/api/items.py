from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.crud.items import (
    count_items,
    count_items_by_language,
    count_items_by_source,
    get_item,
    list_items,
)
from cybersec_api.db.session import get_session
from cybersec_api.schemas.item import (
    ItemLanguageCountRead,
    ItemRead,
    ItemSourceCountRead,
    ItemStatsRead,
)

router = APIRouter(prefix="/items", tags=["items"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
ItemLimit = Annotated[int, Query(ge=1, le=500)]
ItemOffset = Annotated[int, Query(ge=0)]
ItemSearch = Annotated[str | None, Query(min_length=2, max_length=120)]


@router.get("", response_model=list[ItemRead])
async def read_items(
    session: DatabaseSession,
    source_id: UUID | None = None,
    status: str | None = None,
    language: str | None = None,
    is_duplicate: bool | None = None,
    search: ItemSearch = None,
    limit: ItemLimit = 50,
    offset: ItemOffset = 0,
) -> list[ItemRead]:
    return await list_items(
        session,
        source_id=source_id,
        status=status,
        language=language,
        is_duplicate=is_duplicate,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=ItemStatsRead)
async def read_item_stats(session: DatabaseSession) -> ItemStatsRead:
    language_counts = await count_items_by_language(session)
    source_counts = await count_items_by_source(session)

    return ItemStatsRead(
        total=await count_items(session),
        raw=await count_items(session, status="raw"),
        normalized=await count_items(session, status="normalized"),
        duplicate=await count_items(session, is_duplicate=True),
        normalization_error=await count_items(session, status="normalization_error"),
        languages=[
            ItemLanguageCountRead(language=language, count=count)
            for language, count in language_counts
        ],
        sources=[
            ItemSourceCountRead(
                source_id=source_id,
                source_name=source_name,
                count=count,
                last_collected_at=last_collected_at,
            )
            for source_id, source_name, count, last_collected_at in source_counts
        ],
    )


@router.get("/{item_id}", response_model=ItemRead)
async def read_item(item_id: UUID, session: DatabaseSession) -> ItemRead:
    item = await get_item(session, item_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return item
