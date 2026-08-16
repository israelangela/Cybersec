"""add enterprise governance

Revision ID: 0008_enterprise_governance
Revises: 0007_alerts_watchlists
Create Date: 2026-08-16 18:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_enterprise_governance"
down_revision: str | None = "0007_alerts_watchlists"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_email", sa.String(length=320), nullable=True),
        sa.Column("risk_appetite", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        "department_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "department_id",
            "user_id",
            name="uq_department_memberships_department_user",
        ),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_type", sa.String(length=50), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "model_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("enrichment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6), nullable=False),
        sa.Column("raw_usage", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["enrichment_id"], ["enrichments.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "operation",
            "resource_type",
            "resource_id",
            name="uq_model_usage_resource",
        ),
    )
    op.create_index("ix_departments_name", "departments", ["name"], unique=True)
    op.create_index("ix_departments_risk_appetite", "departments", ["risk_appetite"])
    op.create_index(
        "ix_department_memberships_department_id",
        "department_memberships",
        ["department_id"],
    )
    op.create_index("ix_department_memberships_user_id", "department_memberships", ["user_id"])
    op.create_index("ix_department_memberships_role", "department_memberships", ["role"])
    op.create_index("ix_audit_events_actor_type", "audit_events", ["actor_type"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_resource_type", "audit_events", ["resource_type"])
    op.create_index("ix_audit_events_outcome", "audit_events", ["outcome"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])
    op.create_index("ix_model_usage_provider", "model_usage", ["provider"])
    op.create_index("ix_model_usage_model", "model_usage", ["model"])
    op.create_index("ix_model_usage_operation", "model_usage", ["operation"])
    op.create_index("ix_model_usage_resource_type", "model_usage", ["resource_type"])
    op.create_index("ix_model_usage_resource_id", "model_usage", ["resource_id"])
    op.create_index("ix_model_usage_enrichment_id", "model_usage", ["enrichment_id"])
    op.create_index("ix_model_usage_created_at", "model_usage", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_model_usage_created_at", table_name="model_usage")
    op.drop_index("ix_model_usage_enrichment_id", table_name="model_usage")
    op.drop_index("ix_model_usage_resource_id", table_name="model_usage")
    op.drop_index("ix_model_usage_resource_type", table_name="model_usage")
    op.drop_index("ix_model_usage_operation", table_name="model_usage")
    op.drop_index("ix_model_usage_model", table_name="model_usage")
    op.drop_index("ix_model_usage_provider", table_name="model_usage")
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_outcome", table_name="audit_events")
    op.drop_index("ix_audit_events_resource_type", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_type", table_name="audit_events")
    op.drop_index("ix_department_memberships_role", table_name="department_memberships")
    op.drop_index("ix_department_memberships_user_id", table_name="department_memberships")
    op.drop_index("ix_department_memberships_department_id", table_name="department_memberships")
    op.drop_index("ix_departments_risk_appetite", table_name="departments")
    op.drop_index("ix_departments_name", table_name="departments")
    op.drop_table("model_usage")
    op.drop_table("audit_events")
    op.drop_table("department_memberships")
    op.drop_table("departments")
