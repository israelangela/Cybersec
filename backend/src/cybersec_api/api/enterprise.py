from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.db.session import get_session
from cybersec_api.enterprise.service import (
    ROLE_DESCRIPTIONS,
    ROLE_PERMISSIONS,
    build_enterprise_overview,
    create_audit_event,
    create_department,
    create_membership,
    create_user,
    delete_department,
    delete_membership,
    delete_user,
    get_department,
    get_membership,
    get_user,
    list_audit_events,
    list_departments,
    list_memberships,
    list_model_usage,
    list_users,
    sync_model_usage,
    update_department,
    update_membership,
    update_user,
)
from cybersec_api.schemas.enterprise import (
    AuditEventCreate,
    AuditEventRead,
    DepartmentCreate,
    DepartmentMembershipCreate,
    DepartmentMembershipRead,
    DepartmentMembershipUpdate,
    DepartmentRead,
    DepartmentUpdate,
    EnterpriseOverviewRead,
    EnterpriseRoleRead,
    EnterpriseUserCreate,
    EnterpriseUserRead,
    EnterpriseUserUpdate,
    ModelUsageRead,
    ModelUsageSyncRead,
)

router = APIRouter(prefix="/enterprise", tags=["enterprise"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
Limit = Annotated[int, Query(ge=1, le=500)]
Offset = Annotated[int, Query(ge=0)]


@router.get("/overview", response_model=EnterpriseOverviewRead)
async def read_enterprise_overview(session: DatabaseSession) -> EnterpriseOverviewRead:
    return await build_enterprise_overview(session)


@router.get("/roles", response_model=list[EnterpriseRoleRead])
async def read_enterprise_roles() -> list[EnterpriseRoleRead]:
    return [
        EnterpriseRoleRead(
            role=role,
            permissions=permissions,
            description=ROLE_DESCRIPTIONS[role],
        )
        for role, permissions in ROLE_PERMISSIONS.items()
    ]


@router.post("/users", response_model=EnterpriseUserRead, status_code=status.HTTP_201_CREATED)
async def add_enterprise_user(
    payload: EnterpriseUserCreate,
    session: DatabaseSession,
) -> EnterpriseUserRead:
    try:
        return await create_user(session, payload)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User email already exists",
        ) from exc


@router.get("/users", response_model=list[EnterpriseUserRead])
async def read_enterprise_users(
    session: DatabaseSession,
    is_active: bool | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[EnterpriseUserRead]:
    return await list_users(session, is_active=is_active, limit=limit, offset=offset)


@router.patch("/users/{user_id}", response_model=EnterpriseUserRead)
async def patch_enterprise_user(
    user_id: UUID,
    payload: EnterpriseUserUpdate,
    session: DatabaseSession,
) -> EnterpriseUserRead:
    user = await get_user(session, user_id)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        return await update_user(session, user, payload)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User email already exists",
        ) from exc


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_enterprise_user(user_id: UUID, session: DatabaseSession) -> Response:
    deleted = await delete_user(session, user_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/departments",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_department(payload: DepartmentCreate, session: DatabaseSession) -> DepartmentRead:
    try:
        return await create_department(session, payload)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department name already exists",
        ) from exc


@router.get("/departments", response_model=list[DepartmentRead])
async def read_departments(
    session: DatabaseSession,
    is_active: bool | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[DepartmentRead]:
    return await list_departments(session, is_active=is_active, limit=limit, offset=offset)


@router.patch("/departments/{department_id}", response_model=DepartmentRead)
async def patch_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    session: DatabaseSession,
) -> DepartmentRead:
    department = await get_department(session, department_id)

    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    try:
        return await update_department(session, department, payload)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department name already exists",
        ) from exc


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_department(department_id: UUID, session: DatabaseSession) -> Response:
    deleted = await delete_department(session, department_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/departments/{department_id}/memberships",
    response_model=DepartmentMembershipRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_department_membership(
    department_id: UUID,
    payload: DepartmentMembershipCreate,
    session: DatabaseSession,
) -> DepartmentMembershipRead:
    if await get_department(session, department_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    try:
        return await create_membership(session, department_id, payload)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership already exists or user was not found",
        ) from exc


@router.get("/memberships", response_model=list[DepartmentMembershipRead])
async def read_department_memberships(
    session: DatabaseSession,
    department_id: UUID | None = None,
    user_id: UUID | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[DepartmentMembershipRead]:
    return await list_memberships(
        session,
        department_id=department_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.patch("/memberships/{membership_id}", response_model=DepartmentMembershipRead)
async def patch_department_membership(
    membership_id: UUID,
    payload: DepartmentMembershipUpdate,
    session: DatabaseSession,
) -> DepartmentMembershipRead:
    membership = await get_membership(session, membership_id)

    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    return await update_membership(session, membership, payload)


@router.delete("/memberships/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_department_membership(membership_id: UUID, session: DatabaseSession) -> Response:
    deleted = await delete_membership(session, membership_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/audit-events", response_model=AuditEventRead, status_code=status.HTTP_201_CREATED)
async def add_audit_event(payload: AuditEventCreate, session: DatabaseSession) -> AuditEventRead:
    return await create_audit_event(session, payload)


@router.get("/audit-events", response_model=list[AuditEventRead])
async def read_audit_events(
    session: DatabaseSession,
    action: str | None = None,
    resource_type: str | None = None,
    outcome: str | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[AuditEventRead]:
    return await list_audit_events(
        session,
        action=action,
        resource_type=resource_type,
        outcome=outcome,
        limit=limit,
        offset=offset,
    )


@router.post("/model-usage/sync", response_model=ModelUsageSyncRead)
async def sync_enterprise_model_usage(
    session: DatabaseSession,
    limit: Limit = 500,
) -> ModelUsageSyncRead:
    return await sync_model_usage(session, limit=limit)


@router.get("/model-usage", response_model=list[ModelUsageRead])
async def read_model_usage(
    session: DatabaseSession,
    provider: str | None = None,
    model: str | None = None,
    operation: str | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[ModelUsageRead]:
    return await list_model_usage(
        session,
        provider=provider,
        model=model,
        operation=operation,
        limit=limit,
        offset=offset,
    )
