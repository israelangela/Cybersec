"""add stories and pgvector embeddings

Revision ID: 0005_stories
Revises: 0004_cyber_entities
Create Date: 2026-08-16 15:25:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0005_stories"
down_revision: str | None = "0004_cyber_entities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "stories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("entity_count", sa.Integer(), nullable=False),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("entity_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "story_items",
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relevance_score", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("story_id", "item_id"),
    )
    op.create_index("ix_stories_entity_fingerprint", "stories", ["entity_fingerprint"])
    op.create_index("ix_stories_risk_score", "stories", ["risk_score"])
    op.create_index("ix_stories_severity", "stories", ["severity"])
    op.create_index("ix_story_items_item_id", "story_items", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_story_items_item_id", table_name="story_items")
    op.drop_index("ix_stories_severity", table_name="stories")
    op.drop_index("ix_stories_risk_score", table_name="stories")
    op.drop_index("ix_stories_entity_fingerprint", table_name="stories")
    op.drop_table("story_items")
    op.drop_table("stories")
