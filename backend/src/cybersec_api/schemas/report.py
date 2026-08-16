from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from cybersec_api.schemas.item import ItemRead
from cybersec_api.schemas.story import StoryRead


class ReportGenerateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    report_type: str = Field(default="executive", max_length=50)
    severity: str | None = Field(default=None, max_length=20)
    min_score: int | None = Field(default=None, ge=1, le=100)
    story_ids: list[UUID] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=20)


class ReportRead(BaseModel):
    id: UUID
    title: str
    report_type: str
    status: str
    summary: str | None
    severity: str | None
    risk_score: int
    story_count: int
    item_count: int
    entity_count: int
    source_count: int
    period_start: datetime | None
    period_end: datetime | None
    filters: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportStoryRead(BaseModel):
    story_id: UUID
    position: int
    story: StoryRead

    model_config = ConfigDict(from_attributes=True)


class ReportItemRead(BaseModel):
    item_id: UUID
    citation_id: str
    item: ItemRead

    model_config = ConfigDict(from_attributes=True)


class ReportDetailRead(ReportRead):
    body_markdown: str
    stories: list[ReportStoryRead]
    items: list[ReportItemRead]


class ReportGenerateResponse(BaseModel):
    status: str
    report: ReportDetailRead
