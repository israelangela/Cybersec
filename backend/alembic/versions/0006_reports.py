"""add reports

Revision ID: 0006_reports
Revises: 0005_stories
Create Date: 2026-08-16 16:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_reports"
down_revision: str | None = "0005_stories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body_markdown", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("story_count", sa.Integer(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("entity_count", sa.Integer(), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        "report_stories",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("report_id", "story_id"),
    )
    op.create_table(
        "report_items",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("citation_id", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("report_id", "item_id"),
    )
    op.create_index("ix_reports_report_type", "reports", ["report_type"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_severity", "reports", ["severity"])
    op.create_index("ix_reports_risk_score", "reports", ["risk_score"])
    op.create_index("ix_report_stories_story_id", "report_stories", ["story_id"])
    op.create_index("ix_report_items_item_id", "report_items", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_report_items_item_id", table_name="report_items")
    op.drop_index("ix_report_stories_story_id", table_name="report_stories")
    op.drop_index("ix_reports_risk_score", table_name="reports")
    op.drop_index("ix_reports_severity", table_name="reports")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_index("ix_reports_report_type", table_name="reports")
    op.drop_table("report_items")
    op.drop_table("report_stories")
    op.drop_table("reports")
