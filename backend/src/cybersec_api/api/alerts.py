from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.alerts.service import (
    create_watchlist,
    delete_watchlist,
    get_alert,
    get_watchlist,
    list_alerts,
    list_watchlists,
    sync_alerts,
    update_alert_status,
    update_watchlist,
)
from cybersec_api.db.session import get_session
from cybersec_api.schemas.alert import (
    AlertRead,
    AlertStatusUpdate,
    AlertSyncResultRead,
    WatchlistCreate,
    WatchlistRead,
    WatchlistUpdate,
)

router = APIRouter(tags=["alerts"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
Limit = Annotated[int, Query(ge=1, le=500)]
Offset = Annotated[int, Query(ge=0)]


@router.post("/watchlists", response_model=WatchlistRead, status_code=status.HTTP_201_CREATED)
async def create_watchlist_route(
    payload: WatchlistCreate,
    session: DatabaseSession,
) -> WatchlistRead:
    return await create_watchlist(session, payload)


@router.get("/watchlists", response_model=list[WatchlistRead])
async def read_watchlists(
    session: DatabaseSession,
    is_enabled: bool | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[WatchlistRead]:
    return await list_watchlists(session, is_enabled=is_enabled, limit=limit, offset=offset)


@router.patch("/watchlists/{watchlist_id}", response_model=WatchlistRead)
async def patch_watchlist(
    watchlist_id: UUID,
    payload: WatchlistUpdate,
    session: DatabaseSession,
) -> WatchlistRead:
    watchlist = await get_watchlist(session, watchlist_id)

    if watchlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")

    return await update_watchlist(session, watchlist, payload)


@router.delete("/watchlists/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watchlist(watchlist_id: UUID, session: DatabaseSession) -> Response:
    deleted = await delete_watchlist(session, watchlist_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/alerts/sync", response_model=AlertSyncResultRead)
async def sync_alert_signals(session: DatabaseSession, limit: Limit = 500) -> AlertSyncResultRead:
    return await sync_alerts(session, limit=limit)


@router.get("/alerts", response_model=list[AlertRead])
async def read_alerts(
    session: DatabaseSession,
    status: str | None = None,
    severity: str | None = None,
    watchlist_id: UUID | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[AlertRead]:
    return await list_alerts(
        session,
        status=status,
        severity=severity,
        watchlist_id=watchlist_id,
        limit=limit,
        offset=offset,
    )


@router.patch("/alerts/{alert_id}/status", response_model=AlertRead)
async def patch_alert_status(
    alert_id: UUID,
    payload: AlertStatusUpdate,
    session: DatabaseSession,
) -> AlertRead:
    alert = await get_alert(session, alert_id)

    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return await update_alert_status(session, alert, payload.status)
