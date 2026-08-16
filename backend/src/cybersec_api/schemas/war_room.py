from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WarRoomSummaryRead(BaseModel):
    active_stories: int
    critical_stories: int
    high_risk_entities: int
    enriched_items: int
    fresh_items_24h: int
    stale_sources: int
    max_story_risk_score: int
    operation_mode: str


class WarRoomRiskStoryRead(BaseModel):
    id: UUID
    title: str
    summary: str | None
    severity: str | None
    risk_score: int
    item_count: int
    entity_count: int
    keywords: list[str]
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    urgency: str


class WarRoomEntityPulseRead(BaseModel):
    entity_type: str
    normalized_value: str
    occurrences: int
    max_risk_score: int
    severity: str | None
    last_seen_at: datetime | None


class WarRoomTimelineEventRead(BaseModel):
    event_type: str
    title: str
    description: str | None
    severity: str | None
    risk_score: int | None
    occurred_at: datetime | None
    story_id: UUID | None = None
    item_id: UUID | None = None
    source_name: str | None = None


class WarRoomSourceHealthRead(BaseModel):
    id: UUID
    name: str
    source_type: str
    is_enabled: bool
    status: str
    last_fetched_at: datetime | None
    error_count: int
    last_error: str | None


class WarRoomRead(BaseModel):
    summary: WarRoomSummaryRead
    risk_queue: list[WarRoomRiskStoryRead]
    entity_pulse: list[WarRoomEntityPulseRead]
    timeline: list[WarRoomTimelineEventRead]
    source_health: list[WarRoomSourceHealthRead]
