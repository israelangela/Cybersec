from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersec_api.db.base import Base

if TYPE_CHECKING:
    from cybersec_api.models.enrichment import Enrichment
    from cybersec_api.models.item import Item


class CyberEntity(Base):
    __tablename__ = "cyber_entities"
    __table_args__ = (
        UniqueConstraint(
            "item_id",
            "entity_type",
            "normalized_value",
            name="uq_cyber_entities_item_type_value",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    enrichment_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("enrichments.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    severity: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    item: Mapped[Item] = relationship(back_populates="cyber_entities")
    enrichment: Mapped[Enrichment] = relationship(back_populates="cyber_entities")
