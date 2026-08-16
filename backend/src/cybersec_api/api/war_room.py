from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.db.session import get_session
from cybersec_api.schemas.war_room import WarRoomRead
from cybersec_api.war_room.service import build_war_room

router = APIRouter(prefix="/war-room", tags=["war-room"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
WarRoomLimit = Annotated[int, Query(ge=1, le=25)]


@router.get("", response_model=WarRoomRead)
async def read_war_room(
    session: DatabaseSession,
    limit: WarRoomLimit = 10,
) -> WarRoomRead:
    return await build_war_room(session, limit=limit)
