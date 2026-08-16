from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemNormalizationResultRead(BaseModel):
    item_id: UUID
    status: str
    language: str | None = None
    normalized_hash: str | None = None
    duplicate_of_item_id: UUID | None = None
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class NormalizationRunResultRead(BaseModel):
    status: str
    candidates: int
    normalized: int
    duplicates: int
    failed: int
    skipped: int
    results: list[ItemNormalizationResultRead]

    model_config = ConfigDict(from_attributes=True)


class ItemNormalizationRead(ItemNormalizationResultRead):
    normalized_at: datetime | None = None
