from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    entity_type: str | None = Field(default=None, max_length=50)
    value_pattern: str | None = Field(default=None, max_length=255)
    severity: str | None = Field(default=None, max_length=20)
    min_risk_score: int = Field(default=70, ge=1, le=100)
    is_enabled: bool = True


class WatchlistUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    entity_type: str | None = Field(default=None, max_length=50)
    value_pattern: str | None = Field(default=None, max_length=255)
    severity: str | None = Field(default=None, max_length=20)
    min_risk_score: int | None = Field(default=None, ge=1, le=100)
    is_enabled: bool | None = None


class WatchlistRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    entity_type: str | None
    value_pattern: str | None
    severity: str | None
    min_risk_score: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertRead(BaseModel):
    id: UUID
    watchlist_id: UUID
    item_id: UUID
    story_id: UUID | None
    title: str
    description: str | None
    status: str
    severity: str | None
    risk_score: int
    entity_type: str
    entity_value: str
    evidence: dict[str, Any]
    matched_at: datetime | None
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|acknowledged|resolved|dismissed)$")


class AlertSyncResultRead(BaseModel):
    status: str
    watchlists_checked: int
    alerts_created: int
    skipped: int
