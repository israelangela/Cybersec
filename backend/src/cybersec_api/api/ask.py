from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.ask.service import ask_cybersec
from cybersec_api.db.session import get_session
from cybersec_api.schemas.ask import AskRequest, AskResponse

router = APIRouter(prefix="/ask", tags=["ask"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=AskResponse)
async def ask_question(payload: AskRequest, session: DatabaseSession) -> AskResponse:
    return await ask_cybersec(
        session,
        question=payload.question,
        limit=payload.limit,
        use_ai=payload.use_ai,
    )
