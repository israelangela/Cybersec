from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    owner_email: str | None = Field(default=None, max_length=320)
    risk_appetite: str = Field(default="medium", max_length=50)
    is_active: bool = True


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    owner_email: str | None = Field(default=None, max_length=320)
    risk_appetite: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class DepartmentRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    owner_email: str | None
    risk_appetite: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnterpriseUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False


class EnterpriseUserUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=320)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None


class EnterpriseUserRead(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentMembershipCreate(BaseModel):
    user_id: UUID
    role: str = Field(min_length=1, max_length=50)
    permissions: list[str] = Field(default_factory=list)
    is_active: bool = True


class DepartmentMembershipUpdate(BaseModel):
    role: str | None = Field(default=None, min_length=1, max_length=50)
    permissions: list[str] | None = None
    is_active: bool | None = None


class DepartmentMembershipRead(BaseModel):
    id: UUID
    department_id: UUID
    user_id: UUID
    role: str
    permissions: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventCreate(BaseModel):
    actor_type: str = Field(default="system", max_length=50)
    actor_id: str | None = Field(default=None, max_length=255)
    action: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str | None = Field(default=None, max_length=255)
    outcome: str = Field(default="success", max_length=50)
    ip_address: str | None = Field(default=None, max_length=64)
    user_agent: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEventRead(BaseModel):
    id: UUID
    actor_type: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    outcome: str
    ip_address: str | None
    user_agent: str | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ModelUsageRead(BaseModel):
    id: UUID
    provider: str
    model: str
    operation: str
    resource_type: str
    resource_id: str
    enrichment_id: UUID | None
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal
    raw_usage: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelUsageSyncRead(BaseModel):
    status: str
    enrichments_checked: int
    usage_created: int
    skipped: int


class EnterpriseRoleRead(BaseModel):
    role: str
    permissions: list[str]
    description: str


class EnterpriseOverviewRead(BaseModel):
    departments: int
    active_departments: int
    users: int
    active_users: int
    memberships: int
    audit_events: int
    model_usage_records: int
    estimated_cost_usd: Decimal
    open_alerts: int
    critical_open_alerts: int
    recent_audit_events: list[AuditEventRead]
    recent_model_usage: list[ModelUsageRead]
