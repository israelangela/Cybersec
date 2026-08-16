from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersec_api.db.base import Base

if TYPE_CHECKING:
    from cybersec_api.models.item import Item


class Enrichment(Base):
    __tablename__ = "enrichments"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), unique=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    cves: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    iocs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    mitre_attack: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    recommended_actions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    raw_response: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    item: Mapped[Item] = relationship(back_populates="enrichment")
