from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1_000)
    limit: int = Field(default=6, ge=1, le=12)
    use_ai: bool = True


class AskCitationRead(BaseModel):
    citation_id: str
    item_id: UUID
    story_ids: list[UUID]
    title: str
    url: str
    source_name: str | None
    published_at: datetime | None
    collected_at: datetime
    score: float
    excerpt: str
    entities: list[str]


class AskResponse(BaseModel):
    answer: str
    mode: str
    confidence: int
    citations: list[AskCitationRead]
    follow_up_questions: list[str]
