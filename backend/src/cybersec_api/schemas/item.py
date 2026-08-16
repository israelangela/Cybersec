from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemRead(BaseModel):
    id: UUID
    source_id: UUID
    source_name: str | None = None
    title: str
    url: str
    external_id: str | None
    content_hash: str
    summary: str | None
    raw_content: str | None
    status: str
    normalized_title: str | None
    normalized_content: str | None
    normalized_hash: str | None
    language: str | None
    is_duplicate: bool
    duplicate_of_item_id: UUID | None
    normalization_error: str | None
    normalized_at: datetime | None
    published_at: datetime | None
    collected_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemLanguageCountRead(BaseModel):
    language: str
    count: int


class ItemSourceCountRead(BaseModel):
    source_id: UUID
    source_name: str
    count: int
    last_collected_at: datetime | None


class ItemStatsRead(BaseModel):
    total: int
    raw: int
    normalized: int
    duplicate: int
    normalization_error: int
    languages: list[ItemLanguageCountRead]
    sources: list[ItemSourceCountRead]
