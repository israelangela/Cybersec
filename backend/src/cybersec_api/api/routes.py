from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.db.session import get_session

router = APIRouter()
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "cybersec-api"}


@router.get("/ready", tags=["system"])
async def ready(session: DatabaseSession) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
