from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.models.alert import Alert
from cybersec_api.models.enrichment import Enrichment
from cybersec_api.models.enterprise import AuditEvent, Department, DepartmentMembership, ModelUsage
from cybersec_api.models.user import User

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "owner": [
        "sources:manage",
        "pipeline:run",
        "intelligence:read",
        "reports:manage",
        "alerts:triage",
        "enterprise:manage",
    ],
    "security_lead": [
        "sources:manage",
        "pipeline:run",
        "intelligence:read",
        "reports:manage",
        "alerts:triage",
    ],
    "analyst": [
        "pipeline:run",
        "intelligence:read",
        "reports:manage",
        "alerts:triage",
    ],
    "viewer": ["intelligence:read"],
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    "owner": "Full governance role for platform and department administration.",
    "security_lead": "Operational lead role for CTI workflows and alert triage.",
    "analyst": "Day-to-day CTI analyst role for enrichment, reports and alerts.",
    "viewer": "Read-only role for reviewing intelligence and evidence.",
}


@dataclass(slots=True)
class ModelUsageSyncResult:
    status: str
    enrichments_checked: int
    usage_created: int
    skipped: int


def placeholder_password_hash() -> str:
    return "phase12-enterprise-identity-not-a-login-secret"


async def create_user(session: AsyncSession, payload) -> User:
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=placeholder_password_hash(),
        is_active=payload.is_active,
        is_superuser=payload.is_superuser,
    )
    session.add(user)
    await session.flush()
    await record_audit_event(
        session,
        action="user.created",
        resource_type="user",
        resource_id=str(user.id),
        metadata={"email": user.email},
    )
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, user: User, payload) -> User:
    changes = payload.model_dump(exclude_unset=True)

    if "email" in changes and changes["email"] is not None:
        changes["email"] = changes["email"].lower()

    for field, value in changes.items():
        setattr(user, field, value)

    await record_audit_event(
        session,
        action="user.updated",
        resource_type="user",
        resource_id=str(user.id),
        metadata={"fields": sorted(changes.keys())},
    )
    await session.commit()
    await session.refresh(user)
    return user


async def list_users(
    session: AsyncSession,
    *,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[User]:
    statement = select(User).order_by(User.email)

    if is_active is not None:
        statement = statement.where(User.is_active.is_(is_active))

    return list((await session.scalars(statement.offset(offset).limit(limit))).all())


async def get_user(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.scalar(select(User).where(User.id == user_id))


async def delete_user(session: AsyncSession, user_id: UUID) -> bool:
    user = await get_user(session, user_id)

    if user is None:
        return False

    await session.delete(user)
    await record_audit_event(
        session,
        action="user.deleted",
        resource_type="user",
        resource_id=str(user_id),
        metadata={"email": user.email},
    )
    await session.commit()
    return True


async def create_department(session: AsyncSession, payload) -> Department:
    department = Department(**payload.model_dump())
    session.add(department)
    await session.flush()
    await record_audit_event(
        session,
        action="department.created",
        resource_type="department",
        resource_id=str(department.id),
        metadata={"name": department.name},
    )
    await session.commit()
    await session.refresh(department)
    return department


async def update_department(session: AsyncSession, department: Department, payload) -> Department:
    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(department, field, value)

    await record_audit_event(
        session,
        action="department.updated",
        resource_type="department",
        resource_id=str(department.id),
        metadata={"fields": sorted(changes.keys())},
    )
    await session.commit()
    await session.refresh(department)
    return department


async def list_departments(
    session: AsyncSession,
    *,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Department]:
    statement = select(Department).order_by(Department.name)

    if is_active is not None:
        statement = statement.where(Department.is_active.is_(is_active))

    return list((await session.scalars(statement.offset(offset).limit(limit))).all())


async def get_department(session: AsyncSession, department_id: UUID) -> Department | None:
    return await session.scalar(select(Department).where(Department.id == department_id))


async def delete_department(session: AsyncSession, department_id: UUID) -> bool:
    department = await get_department(session, department_id)

    if department is None:
        return False

    await session.delete(department)
    await record_audit_event(
        session,
        action="department.deleted",
        resource_type="department",
        resource_id=str(department_id),
        metadata={"name": department.name},
    )
    await session.commit()
    return True


def role_permissions(role: str, explicit_permissions: list[str] | None = None) -> list[str]:
    if explicit_permissions:
        return sorted(set(explicit_permissions))

    return ROLE_PERMISSIONS.get(role, [])


async def create_membership(
    session: AsyncSession,
    department_id: UUID,
    payload,
) -> DepartmentMembership:
    membership = DepartmentMembership(
        department_id=department_id,
        user_id=payload.user_id,
        role=payload.role,
        permissions=role_permissions(payload.role, payload.permissions),
        is_active=payload.is_active,
    )
    session.add(membership)
    await session.flush()
    await record_audit_event(
        session,
        action="department.membership.created",
        resource_type="department_membership",
        resource_id=str(membership.id),
        metadata={
            "department_id": str(department_id),
            "user_id": str(payload.user_id),
            "role": payload.role,
        },
    )
    await session.commit()
    await session.refresh(membership)
    return membership


async def update_membership(
    session: AsyncSession,
    membership: DepartmentMembership,
    payload,
) -> DepartmentMembership:
    changes = payload.model_dump(exclude_unset=True)

    if "role" in changes and "permissions" not in changes:
        changes["permissions"] = role_permissions(changes["role"])

    for field, value in changes.items():
        setattr(membership, field, value)

    await record_audit_event(
        session,
        action="department.membership.updated",
        resource_type="department_membership",
        resource_id=str(membership.id),
        metadata={"fields": sorted(changes.keys())},
    )
    await session.commit()
    await session.refresh(membership)
    return membership


async def list_memberships(
    session: AsyncSession,
    *,
    department_id: UUID | None = None,
    user_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[DepartmentMembership]:
    statement = select(DepartmentMembership).order_by(DepartmentMembership.created_at.desc())

    if department_id is not None:
        statement = statement.where(DepartmentMembership.department_id == department_id)

    if user_id is not None:
        statement = statement.where(DepartmentMembership.user_id == user_id)

    return list((await session.scalars(statement.offset(offset).limit(limit))).all())


async def get_membership(
    session: AsyncSession,
    membership_id: UUID,
) -> DepartmentMembership | None:
    return await session.scalar(
        select(DepartmentMembership).where(DepartmentMembership.id == membership_id)
    )


async def delete_membership(session: AsyncSession, membership_id: UUID) -> bool:
    result = await session.execute(
        delete(DepartmentMembership).where(DepartmentMembership.id == membership_id)
    )

    if not result.rowcount:
        await session.rollback()
        return False

    await record_audit_event(
        session,
        action="department.membership.deleted",
        resource_type="department_membership",
        resource_id=str(membership_id),
    )
    await session.commit()
    return bool(result.rowcount)


async def record_audit_event(
    session: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    actor_type: str = "system",
    actor_id: str | None = None,
    outcome: str = "success",
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_=metadata or {},
    )
    session.add(event)
    return event


async def create_audit_event(session: AsyncSession, payload) -> AuditEvent:
    event = await record_audit_event(
        session,
        actor_type=payload.actor_type,
        actor_id=payload.actor_id,
        action=payload.action,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        outcome=payload.outcome,
        ip_address=payload.ip_address,
        user_agent=payload.user_agent,
        metadata=payload.metadata,
    )
    await session.commit()
    await session.refresh(event)
    return event


async def list_audit_events(
    session: AsyncSession,
    *,
    action: str | None = None,
    resource_type: str | None = None,
    outcome: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditEvent]:
    statement = select(AuditEvent).order_by(AuditEvent.created_at.desc())

    if action is not None:
        statement = statement.where(AuditEvent.action == action)

    if resource_type is not None:
        statement = statement.where(AuditEvent.resource_type == resource_type)

    if outcome is not None:
        statement = statement.where(AuditEvent.outcome == outcome)

    return list((await session.scalars(statement.offset(offset).limit(limit))).all())


def extract_usage(raw_response: dict) -> tuple[int, int, dict]:
    usage = raw_response.get("usage") if isinstance(raw_response, dict) else None

    if not isinstance(usage, dict):
        return 0, 0, {}

    input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    return input_tokens, output_tokens, usage


def estimated_cost(input_tokens: int, output_tokens: int) -> Decimal:
    total_tokens = input_tokens + output_tokens
    return Decimal(total_tokens) * Decimal("0.000000")


async def sync_model_usage(session: AsyncSession, *, limit: int = 500) -> ModelUsageSyncResult:
    statement = (
        select(Enrichment)
        .where(Enrichment.status == "completed")
        .order_by(Enrichment.enriched_at.desc().nullslast(), Enrichment.created_at.desc())
        .limit(limit)
    )
    enrichments = list((await session.scalars(statement)).all())
    usage_created = 0
    skipped = 0

    for enrichment in enrichments:
        exists = await session.scalar(
            select(ModelUsage.id).where(
                ModelUsage.operation == "enrichment",
                ModelUsage.resource_type == "item",
                ModelUsage.resource_id == str(enrichment.item_id),
            )
        )

        if exists is not None:
            skipped += 1
            continue

        input_tokens, output_tokens, raw_usage = extract_usage(enrichment.raw_response)
        session.add(
            ModelUsage(
                provider=enrichment.provider,
                model=enrichment.model,
                operation="enrichment",
                resource_type="item",
                resource_id=str(enrichment.item_id),
                enrichment_id=enrichment.id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=estimated_cost(input_tokens, output_tokens),
                raw_usage=raw_usage,
            )
        )
        usage_created += 1

    if usage_created:
        await record_audit_event(
            session,
            action="model_usage.synced",
            resource_type="model_usage",
            metadata={"usage_created": usage_created, "enrichments_checked": len(enrichments)},
        )

    await session.commit()
    return ModelUsageSyncResult(
        status="ok",
        enrichments_checked=len(enrichments),
        usage_created=usage_created,
        skipped=skipped,
    )


async def list_model_usage(
    session: AsyncSession,
    *,
    provider: str | None = None,
    model: str | None = None,
    operation: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ModelUsage]:
    statement = select(ModelUsage).order_by(ModelUsage.created_at.desc())

    if provider is not None:
        statement = statement.where(ModelUsage.provider == provider)

    if model is not None:
        statement = statement.where(ModelUsage.model == model)

    if operation is not None:
        statement = statement.where(ModelUsage.operation == operation)

    return list((await session.scalars(statement.offset(offset).limit(limit))).all())


async def scalar_count(session: AsyncSession, statement) -> int:
    return int(await session.scalar(statement) or 0)


async def build_enterprise_overview(session: AsyncSession):
    estimated_total = await session.scalar(
        func.coalesce(func.sum(ModelUsage.estimated_cost_usd), 0)
    )

    return {
        "departments": await scalar_count(session, select(func.count(Department.id))),
        "active_departments": await scalar_count(
            session,
            select(func.count(Department.id)).where(Department.is_active.is_(True)),
        ),
        "users": await scalar_count(session, select(func.count(User.id))),
        "active_users": await scalar_count(
            session,
            select(func.count(User.id)).where(User.is_active.is_(True)),
        ),
        "memberships": await scalar_count(session, select(func.count(DepartmentMembership.id))),
        "audit_events": await scalar_count(session, select(func.count(AuditEvent.id))),
        "model_usage_records": await scalar_count(session, select(func.count(ModelUsage.id))),
        "estimated_cost_usd": estimated_total,
        "open_alerts": await scalar_count(
            session,
            select(func.count(Alert.id)).where(Alert.status == "open"),
        ),
        "critical_open_alerts": await scalar_count(
            session,
            select(func.count(Alert.id)).where(
                Alert.status == "open",
                Alert.severity == "critical",
            ),
        ),
        "recent_audit_events": await list_audit_events(session, limit=8),
        "recent_model_usage": await list_model_usage(session, limit=8),
    }
