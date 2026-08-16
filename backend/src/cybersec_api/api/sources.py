from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.crud.sources import (
    create_source,
    delete_source,
    get_source,
    list_sources,
    update_source,
)
from cybersec_api.db.session import get_session
from cybersec_api.models.source import Source
from cybersec_api.schemas.source import SourceCreate, SourceRead, SourceType, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
SourceTypeFilter = Annotated[SourceType | None, Query()]


async def source_or_404(session: AsyncSession, source_id: UUID) -> Source:
    source = await get_source(session, source_id)

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    return source


@router.get("", response_model=list[SourceRead])
async def read_sources(
    session: DatabaseSession,
    is_enabled: bool | None = None,
    source_type: SourceTypeFilter = None,
) -> list[SourceRead]:
    return await list_sources(session, is_enabled=is_enabled, source_type=source_type)


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
async def add_source(payload: SourceCreate, session: DatabaseSession) -> SourceRead:
    try:
        return await create_source(session, payload)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source URL already exists",
        ) from exc


@router.get("/{source_id}", response_model=SourceRead)
async def read_source(source_id: UUID, session: DatabaseSession) -> SourceRead:
    return await source_or_404(session, source_id)


@router.patch("/{source_id}", response_model=SourceRead)
async def edit_source(
    source_id: UUID,
    payload: SourceUpdate,
    session: DatabaseSession,
) -> SourceRead:
    source = await source_or_404(session, source_id)

    if not payload.model_fields_set:
        return source

    try:
        return await update_source(session, source, payload)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source URL already exists",
        ) from exc


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_source(source_id: UUID, session: DatabaseSession) -> None:
    source = await source_or_404(session, source_id)
    await delete_source(session, source)
