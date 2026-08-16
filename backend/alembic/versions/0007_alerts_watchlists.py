"""add alerts and watchlists

Revision ID: 0007_alerts_watchlists
Revises: 0006_reports
Create Date: 2026-08-16 16:55:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_alerts_watchlists"
down_revision: str | None = "0006_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("value_pattern", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("min_risk_score", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
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
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_value", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["watchlist_id"], ["watchlists.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "watchlist_id",
            "entity_type",
            "entity_value",
            "item_id",
            "story_id",
            name="uq_alerts_watchlist_signal",
        ),
    )
    op.create_index("ix_watchlists_entity_type", "watchlists", ["entity_type"])
    op.create_index("ix_watchlists_severity", "watchlists", ["severity"])
    op.create_index("ix_alerts_watchlist_id", "alerts", ["watchlist_id"])
    op.create_index("ix_alerts_item_id", "alerts", ["item_id"])
    op.create_index("ix_alerts_story_id", "alerts", ["story_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_risk_score", "alerts", ["risk_score"])
    op.create_index("ix_alerts_entity_type", "alerts", ["entity_type"])


def downgrade() -> None:
    op.drop_index("ix_alerts_entity_type", table_name="alerts")
    op.drop_index("ix_alerts_risk_score", table_name="alerts")
    op.drop_index("ix_alerts_severity", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_story_id", table_name="alerts")
    op.drop_index("ix_alerts_item_id", table_name="alerts")
    op.drop_index("ix_alerts_watchlist_id", table_name="alerts")
    op.drop_index("ix_watchlists_severity", table_name="watchlists")
    op.drop_index("ix_watchlists_entity_type", table_name="watchlists")
    op.drop_table("alerts")
    op.drop_table("watchlists")
