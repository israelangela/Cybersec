from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.db.session import get_session

router = APIRouter(tags=["system"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "cybersec-api"}


@router.get("/ready")
async def ready(session: DatabaseSession) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
