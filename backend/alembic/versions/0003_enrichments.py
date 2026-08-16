"""Add item enrichments

Revision ID: 0003_enrichments
Revises: 0002_item_normalization
Create Date: 2026-08-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_enrichments"
down_revision: str | None = "0002_item_normalization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_column(name: str) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "enrichments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cves", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("iocs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("mitre_attack", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommended_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("enriched_at", sa.DateTime(timezone=True), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id"),
    )
    op.create_index(op.f("ix_enrichments_item_id"), "enrichments", ["item_id"], unique=True)
    op.create_index(op.f("ix_enrichments_status"), "enrichments", ["status"], unique=False)
    op.create_index(op.f("ix_enrichments_severity"), "enrichments", ["severity"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_enrichments_severity"), table_name="enrichments")
    op.drop_index(op.f("ix_enrichments_status"), table_name="enrichments")
    op.drop_index(op.f("ix_enrichments_item_id"), table_name="enrichments")
    op.drop_table("enrichments")
