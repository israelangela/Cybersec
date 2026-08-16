from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersec_api.db.base import Base

if TYPE_CHECKING:
    from cybersec_api.models.enrichment import Enrichment
    from cybersec_api.models.source import Source


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_items_source_external_id"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="raw")
    normalized_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duplicate_of_item_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    normalization_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    source: Mapped[Source] = relationship(back_populates="items")
    enrichment: Mapped[Enrichment | None] = relationship(
        back_populates="item", cascade="all, delete-orphan", uselist=False
    )

    @property
    def source_name(self) -> str | None:
        source = self.__dict__.get("source")
        return source.name if source is not None else None

    @property
    def ai_summary(self) -> str | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.summary if enrichment is not None else None

    @property
    def ai_severity(self) -> str | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.severity if enrichment is not None else None

    @property
    def ai_confidence(self) -> int | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.confidence if enrichment is not None else None

    @property
    def ai_tags(self) -> list[str] | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.tags if enrichment is not None else None

    @property
    def ai_cves(self) -> list[str] | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.cves if enrichment is not None else None

    @property
    def ai_iocs(self) -> list[str] | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.iocs if enrichment is not None else None

    @property
    def ai_mitre_attack(self) -> list[str] | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.mitre_attack if enrichment is not None else None

    @property
    def ai_recommended_actions(self) -> list[str] | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.recommended_actions if enrichment is not None else None

    @property
    def enriched_at(self) -> datetime | None:
        enrichment = self.__dict__.get("enrichment")
        return enrichment.enriched_at if enrichment is not None else None
