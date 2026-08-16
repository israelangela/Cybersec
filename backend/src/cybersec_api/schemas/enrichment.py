from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIEnrichmentPayload(BaseModel):
    summary: str = Field(min_length=1, max_length=1200)
    severity: str
    confidence: int = Field(ge=0, le=100)
    tags: list[str] = Field(default_factory=list)
    cves: list[str] = Field(default_factory=list)
    iocs: list[str] = Field(default_factory=list)
    mitre_attack: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class EnrichmentRead(BaseModel):
    id: UUID
    item_id: UUID
    provider: str
    model: str
    status: str
    summary: str | None
    severity: str | None
    confidence: int | None
    tags: list[str]
    cves: list[str]
    iocs: list[str]
    mitre_attack: list[str]
    recommended_actions: list[str]
    error: str | None
    enriched_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemEnrichmentResultRead(BaseModel):
    item_id: UUID
    status: str
    enrichment: EnrichmentRead | None = None
    error: str | None = None


class EnrichmentRunResultRead(BaseModel):
    status: str
    candidates: int
    enriched: int
    failed: int
    skipped: int
    results: list[ItemEnrichmentResultRead]
