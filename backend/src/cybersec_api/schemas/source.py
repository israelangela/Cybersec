from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

SourceType = Literal["rss", "web", "api", "other"]


class SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    source_type: SourceType = "rss"
    description: str | None = Field(default=None, max_length=5000)
    weight: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.00"), le=Decimal("10.00"))
    is_enabled: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    source_type: SourceType | None = None
    description: str | None = Field(default=None, max_length=5000)
    weight: Decimal | None = Field(default=None, ge=Decimal("0.00"), le=Decimal("10.00"))
    is_enabled: bool | None = None


class SourceRead(BaseModel):
    id: UUID
    name: str
    url: str
    source_type: str
    description: str | None
    weight: Decimal
    is_enabled: bool
    last_fetched_at: datetime | None
    last_error: str | None
    error_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
