"""Add item normalization fields

Revision ID: 0002_item_normalization
Revises: 0001_initial
Create Date: 2026-08-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_item_normalization"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("items", sa.Column("normalized_title", sa.Text(), nullable=True))
    op.add_column("items", sa.Column("normalized_content", sa.Text(), nullable=True))
    op.add_column("items", sa.Column("normalized_hash", sa.String(length=64), nullable=True))
    op.add_column("items", sa.Column("language", sa.String(length=16), nullable=True))
    op.add_column(
        "items", sa.Column("is_duplicate", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column(
        "items", sa.Column("duplicate_of_item_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column("items", sa.Column("normalization_error", sa.Text(), nullable=True))
    op.add_column("items", sa.Column("normalized_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_items_normalized_hash"), "items", ["normalized_hash"], unique=False)
    op.create_index(op.f("ix_items_language"), "items", ["language"], unique=False)
    op.create_foreign_key(
        "fk_items_duplicate_of_item_id",
        "items",
        "items",
        ["duplicate_of_item_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_items_duplicate_of_item_id", "items", type_="foreignkey")
    op.drop_index(op.f("ix_items_language"), table_name="items")
    op.drop_index(op.f("ix_items_normalized_hash"), table_name="items")
    op.drop_column("items", "normalized_at")
    op.drop_column("items", "normalization_error")
    op.drop_column("items", "duplicate_of_item_id")
    op.drop_column("items", "is_duplicate")
    op.drop_column("items", "language")
    op.drop_column("items", "normalized_hash")
    op.drop_column("items", "normalized_content")
    op.drop_column("items", "normalized_title")
