from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemRead(BaseModel):
    id: UUID
    source_id: UUID
    title: str
    url: str
    external_id: str | None
    content_hash: str
    summary: str | None
    raw_content: str | None
    status: str
    published_at: datetime | None
    collected_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
