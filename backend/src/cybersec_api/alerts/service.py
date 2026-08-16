from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersec_api.models.alert import Alert, Watchlist
from cybersec_api.models.cyber_entity import CyberEntity
from cybersec_api.models.item import Item


@dataclass(slots=True)
class AlertSyncResult:
    status: str
    watchlists_checked: int
    alerts_created: int
    skipped: int


async def create_watchlist(session: AsyncSession, payload) -> Watchlist:
    watchlist = Watchlist(**payload.model_dump())
    session.add(watchlist)
    await session.commit()
    await session.refresh(watchlist)
    return watchlist


async def update_watchlist(session: AsyncSession, watchlist: Watchlist, payload) -> Watchlist:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(watchlist, field, value)

    await session.commit()
    await session.refresh(watchlist)
    return watchlist


async def list_watchlists(
    session: AsyncSession,
    *,
    is_enabled: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Watchlist]:
    statement = select(Watchlist).order_by(Watchlist.created_at.desc())

    if is_enabled is not None:
        statement = statement.where(Watchlist.is_enabled.is_(is_enabled))

    return list((await session.scalars(statement.offset(offset).limit(limit))).all())


async def get_watchlist(session: AsyncSession, watchlist_id: UUID) -> Watchlist | None:
    return await session.scalar(select(Watchlist).where(Watchlist.id == watchlist_id))


async def delete_watchlist(session: AsyncSession, watchlist_id: UUID) -> bool:
    result = await session.execute(delete(Watchlist).where(Watchlist.id == watchlist_id))
    await session.commit()
    return bool(result.rowcount)


def watchlist_matches_entity(watchlist: Watchlist, entity: CyberEntity) -> bool:
    if watchlist.entity_type and watchlist.entity_type != entity.entity_type:
        return False

    if entity.risk_score < watchlist.min_risk_score:
        return False

    if watchlist.severity and watchlist.severity != entity.severity:
        return False

    if watchlist.value_pattern:
        pattern = watchlist.value_pattern.lower()
        values = [entity.value.lower(), entity.normalized_value.lower()]

        if not any(pattern in value for value in values):
            return False

    return True


def first_story_id(item: Item) -> UUID | None:
    story_items = sorted(item.story_items, key=lambda story_item: story_item.created_at)
    return story_items[0].story_id if story_items else None


async def alert_exists(
    session: AsyncSession,
    *,
    watchlist: Watchlist,
    entity: CyberEntity,
    story_id: UUID | None,
) -> bool:
    statement = select(Alert.id).where(
        and_(
            Alert.watchlist_id == watchlist.id,
            Alert.entity_type == entity.entity_type,
            Alert.entity_value == entity.normalized_value,
            Alert.item_id == entity.item_id,
            Alert.story_id == story_id,
        )
    )
    return await session.scalar(statement) is not None


def build_alert(watchlist: Watchlist, entity: CyberEntity, story_id: UUID | None) -> Alert:
    item = entity.item
    title = f"{watchlist.name}: {entity.normalized_value}"
    item_title = item.normalized_title or item.title
    return Alert(
        watchlist_id=watchlist.id,
        item_id=entity.item_id,
        story_id=story_id,
        title=title,
        description=f"{entity.entity_type} matched in {item_title}",
        status="open",
        severity=entity.severity,
        risk_score=entity.risk_score,
        entity_type=entity.entity_type,
        entity_value=entity.normalized_value,
        evidence={
            "watchlist": watchlist.name,
            "item_title": item_title,
            "source_name": item.source_name,
            "source_url": item.url,
            "entity_value": entity.value,
            "evidence": entity.evidence,
        },
        matched_at=entity.last_seen_at or entity.first_seen_at or item.published_at,
    )


async def sync_alerts(session: AsyncSession, *, limit: int = 500) -> AlertSyncResult:
    watchlists = await list_watchlists(session, is_enabled=True, limit=200)
    statement = (
        select(CyberEntity)
        .options(
            selectinload(CyberEntity.item).selectinload(Item.source),
            selectinload(CyberEntity.item).selectinload(Item.story_items),
        )
        .order_by(CyberEntity.risk_score.desc(), CyberEntity.last_seen_at.desc().nullslast())
        .limit(limit)
    )
    entities = list((await session.scalars(statement)).all())
    alerts_created = 0
    skipped = 0

    for watchlist in watchlists:
        for entity in entities:
            if not watchlist_matches_entity(watchlist, entity):
                skipped += 1
                continue

            story_id = first_story_id(entity.item)

            if await alert_exists(session, watchlist=watchlist, entity=entity, story_id=story_id):
                skipped += 1
                continue

            session.add(build_alert(watchlist, entity, story_id))
            alerts_created += 1

    await session.commit()
    return AlertSyncResult(
        status="ok",
        watchlists_checked=len(watchlists),
        alerts_created=alerts_created,
        skipped=skipped,
    )


async def list_alerts(
    session: AsyncSession,
    *,
    status: str | None = None,
    severity: str | None = None,
    watchlist_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Alert]:
    statement = select(Alert).options(selectinload(Alert.watchlist))

    if status is not None:
        statement = statement.where(Alert.status == status)

    if severity is not None:
        statement = statement.where(Alert.severity == severity)

    if watchlist_id is not None:
        statement = statement.where(Alert.watchlist_id == watchlist_id)

    statement = statement.order_by(Alert.risk_score.desc(), Alert.created_at.desc())
    return list((await session.scalars(statement.offset(offset).limit(limit))).all())


async def get_alert(session: AsyncSession, alert_id: UUID) -> Alert | None:
    return await session.scalar(select(Alert).where(Alert.id == alert_id))


async def update_alert_status(session: AsyncSession, alert: Alert, status: str) -> Alert:
    alert.status = status
    now = datetime.now(UTC)

    if status == "acknowledged":
        alert.acknowledged_at = alert.acknowledged_at or now
    elif status in {"resolved", "dismissed"}:
        alert.resolved_at = alert.resolved_at or now

    await session.commit()
    await session.refresh(alert)
    return alert
