"""add cyber intelligence entities

Revision ID: 0004_cyber_entities
Revises: 0003_enrichments
Create Date: 2026-08-16 14:55:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_cyber_entities"
down_revision: str | None = "0003_enrichments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cyber_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.ForeignKeyConstraint(["enrichment_id"], ["enrichments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "item_id",
            "entity_type",
            "normalized_value",
            name="uq_cyber_entities_item_type_value",
        ),
    )
    op.create_index("ix_cyber_entities_entity_type", "cyber_entities", ["entity_type"])
    op.create_index(
        "ix_cyber_entities_normalized_value", "cyber_entities", ["normalized_value"]
    )
    op.create_index("ix_cyber_entities_risk_score", "cyber_entities", ["risk_score"])
    op.create_index("ix_cyber_entities_severity", "cyber_entities", ["severity"])
    op.create_index("ix_cyber_entities_item_id", "cyber_entities", ["item_id"])
    op.create_index("ix_cyber_entities_enrichment_id", "cyber_entities", ["enrichment_id"])


def downgrade() -> None:
    op.drop_index("ix_cyber_entities_enrichment_id", table_name="cyber_entities")
    op.drop_index("ix_cyber_entities_item_id", table_name="cyber_entities")
    op.drop_index("ix_cyber_entities_severity", table_name="cyber_entities")
    op.drop_index("ix_cyber_entities_risk_score", table_name="cyber_entities")
    op.drop_index("ix_cyber_entities_normalized_value", table_name="cyber_entities")
    op.drop_index("ix_cyber_entities_entity_type", table_name="cyber_entities")
    op.drop_table("cyber_entities")
