from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CyberEntityRead(BaseModel):
    id: UUID
    item_id: UUID
    enrichment_id: UUID
    entity_type: str
    value: str
    normalized_value: str
    severity: str | None
    confidence: int | None
    risk_score: int
    evidence: dict
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CyberEntityAggregateRead(BaseModel):
    entity_type: str
    value: str
    normalized_value: str
    occurrences: int
    max_risk_score: int
    avg_confidence: float | None
    severity: str | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None


class CyberEntityTypeCountRead(BaseModel):
    entity_type: str
    count: int


class CyberEntityRiskRead(BaseModel):
    entity_type: str
    value: str
    normalized_value: str
    risk_score: int
    severity: str | None
    item_id: UUID
    last_seen_at: datetime | None


class IntelligenceStatsRead(BaseModel):
    total_entities: int
    unique_entities: int
    high_risk_entities: int
    by_type: list[CyberEntityTypeCountRead]
    top_risks: list[CyberEntityRiskRead]


class IntelligenceSyncResultRead(BaseModel):
    status: str
    enrichments_checked: int
    entities_created: int
    entities_deleted: int
    skipped: int
