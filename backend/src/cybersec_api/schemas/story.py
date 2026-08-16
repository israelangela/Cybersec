from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from cybersec_api.schemas.item import ItemRead


class StoryItemRead(BaseModel):
    item_id: UUID
    relevance_score: int
    created_at: datetime
    item: ItemRead | None = None

    model_config = ConfigDict(from_attributes=True)


class StoryRead(BaseModel):
    id: UUID
    title: str
    summary: str | None
    status: str
    severity: str | None
    risk_score: int
    item_count: int
    entity_count: int
    keywords: list[str]
    entity_fingerprint: str
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StoryDetailRead(StoryRead):
    items: list[StoryItemRead]


class StorySyncResultRead(BaseModel):
    status: str
    candidates: int
    stories_created: int
    story_items_created: int
    stories_deleted: int
    skipped: int


class StoryStatsRead(BaseModel):
    total_stories: int
    high_risk_stories: int
    linked_items: int
    top_stories: list[StoryRead]
