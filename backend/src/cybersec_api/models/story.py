from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersec_api.db.base import Base

if TYPE_CHECKING:
    from cybersec_api.models.item import Item


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    severity: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    entity_count: Mapped[int] = mapped_column(Integer, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    entity_fingerprint: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    story_items: Mapped[list[StoryItem]] = relationship(
        back_populates="story", cascade="all, delete-orphan"
    )


class StoryItem(Base):
    __tablename__ = "story_items"

    story_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("stories.id", ondelete="CASCADE"),
        primary_key=True,
    )
    item_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("items.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    relevance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    story: Mapped[Story] = relationship(back_populates="story_items")
    item: Mapped[Item] = relationship(back_populates="story_items")
