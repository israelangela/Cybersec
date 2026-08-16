from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersec_api.models.cyber_entity import CyberEntity
from cybersec_api.models.enrichment import Enrichment
from cybersec_api.models.item import Item
from cybersec_api.models.source import Source
from cybersec_api.models.story import Story
from cybersec_api.schemas.war_room import (
    WarRoomEntityPulseRead,
    WarRoomRead,
    WarRoomRiskStoryRead,
    WarRoomSourceHealthRead,
    WarRoomSummaryRead,
    WarRoomTimelineEventRead,
)


def story_urgency(story: Story) -> str:
    if story.risk_score >= 85 or story.severity == "critical":
        return "immediate"

    if story.risk_score >= 70 or story.severity == "high":
        return "priority"

    if story.risk_score >= 45 or story.severity == "medium":
        return "watch"

    return "monitor"


def operation_mode(
    max_story_risk_score: int,
    critical_stories: int,
    high_risk_entities: int,
) -> str:
    if max_story_risk_score >= 85 or critical_stories > 0:
        return "hot"

    if max_story_risk_score >= 70 or high_risk_entities >= 5:
        return "active"

    return "watch"


def source_status(source: Source, stale_threshold: datetime) -> str:
    if not source.is_enabled:
        return "disabled"

    if source.last_error or source.error_count >= 3:
        return "degraded"

    if source.last_fetched_at is None or source.last_fetched_at < stale_threshold:
        return "stale"

    return "healthy"


async def count_scalar(session: AsyncSession, statement) -> int:
    return await session.scalar(statement) or 0


async def load_risk_queue(session: AsyncSession, *, limit: int) -> list[WarRoomRiskStoryRead]:
    statement = (
        select(Story)
        .where(Story.status == "active")
        .order_by(Story.risk_score.desc(), Story.last_seen_at.desc().nullslast())
        .limit(limit)
    )
    stories = list((await session.scalars(statement)).all())
    return [
        WarRoomRiskStoryRead(
            id=story.id,
            title=story.title,
            summary=story.summary,
            severity=story.severity,
            risk_score=story.risk_score,
            item_count=story.item_count,
            entity_count=story.entity_count,
            keywords=story.keywords,
            first_seen_at=story.first_seen_at,
            last_seen_at=story.last_seen_at,
            urgency=story_urgency(story),
        )
        for story in stories
    ]


async def load_entity_pulse(session: AsyncSession, *, limit: int) -> list[WarRoomEntityPulseRead]:
    statement = (
        select(
            CyberEntity.entity_type,
            CyberEntity.normalized_value,
            func.count(CyberEntity.id),
            func.max(CyberEntity.risk_score),
            func.max(CyberEntity.severity),
            func.max(CyberEntity.last_seen_at),
        )
        .group_by(CyberEntity.entity_type, CyberEntity.normalized_value)
        .order_by(func.max(CyberEntity.risk_score).desc(), func.count(CyberEntity.id).desc())
        .limit(limit)
    )
    rows = list((await session.execute(statement)).all())
    return [
        WarRoomEntityPulseRead(
            entity_type=entity_type,
            normalized_value=normalized_value,
            occurrences=occurrences,
            max_risk_score=max_risk_score,
            severity=severity,
            last_seen_at=last_seen_at,
        )
        for (
            entity_type,
            normalized_value,
            occurrences,
            max_risk_score,
            severity,
            last_seen_at,
        ) in rows
    ]


async def load_timeline(session: AsyncSession, *, limit: int) -> list[WarRoomTimelineEventRead]:
    story_statement = (
        select(Story)
        .where(Story.status == "active")
        .order_by(Story.last_seen_at.desc().nullslast(), Story.risk_score.desc())
        .limit(limit)
    )
    item_statement = (
        select(Item)
        .options(selectinload(Item.source), selectinload(Item.enrichment))
        .order_by(Item.published_at.desc().nullslast(), Item.collected_at.desc())
        .limit(limit)
    )

    stories = list((await session.scalars(story_statement)).all())
    items = list((await session.scalars(item_statement)).all())

    events = [
        WarRoomTimelineEventRead(
            event_type="story",
            title=story.title,
            description=story.summary,
            severity=story.severity,
            risk_score=story.risk_score,
            occurred_at=story.last_seen_at or story.created_at,
            story_id=story.id,
        )
        for story in stories
    ]
    events.extend(
        WarRoomTimelineEventRead(
            event_type="item",
            title=item.normalized_title or item.title,
            description=item.ai_summary or item.summary,
            severity=item.ai_severity,
            risk_score=None,
            occurred_at=item.published_at or item.collected_at,
            item_id=item.id,
            source_name=item.source_name,
        )
        for item in items
    )

    return sorted(
        events,
        key=lambda event: event.occurred_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )[:limit]


async def load_source_health(
    session: AsyncSession,
    *,
    limit: int,
    stale_threshold: datetime,
) -> list[WarRoomSourceHealthRead]:
    statement = (
        select(Source)
        .order_by(Source.is_enabled.desc(), Source.error_count.desc(), Source.name.asc())
        .limit(limit)
    )
    sources = list((await session.scalars(statement)).all())
    return [
        WarRoomSourceHealthRead(
            id=source.id,
            name=source.name,
            source_type=source.source_type,
            is_enabled=source.is_enabled,
            status=source_status(source, stale_threshold),
            last_fetched_at=source.last_fetched_at,
            error_count=source.error_count,
            last_error=source.last_error,
        )
        for source in sources
    ]


async def build_war_room(session: AsyncSession, *, limit: int = 10) -> WarRoomRead:
    now = datetime.now(UTC)
    fresh_threshold = now - timedelta(hours=24)
    stale_threshold = now - timedelta(days=7)

    active_stories = await count_scalar(
        session, select(func.count(Story.id)).where(Story.status == "active")
    )
    critical_stories = await count_scalar(
        session,
        select(func.count(Story.id)).where(Story.status == "active", Story.risk_score >= 85),
    )
    high_risk_entities = await count_scalar(
        session, select(func.count(CyberEntity.id)).where(CyberEntity.risk_score >= 70)
    )
    enriched_items = await count_scalar(
        session, select(func.count(Enrichment.id)).where(Enrichment.status == "completed")
    )
    fresh_items_24h = await count_scalar(
        session, select(func.count(Item.id)).where(Item.collected_at >= fresh_threshold)
    )
    stale_sources = await count_scalar(
        session,
        select(func.count(Source.id)).where(
            Source.is_enabled.is_(True),
            (Source.last_fetched_at.is_(None)) | (Source.last_fetched_at < stale_threshold),
        ),
    )
    max_story_risk_score = await count_scalar(session, select(func.max(Story.risk_score)))

    return WarRoomRead(
        summary=WarRoomSummaryRead(
            active_stories=active_stories,
            critical_stories=critical_stories,
            high_risk_entities=high_risk_entities,
            enriched_items=enriched_items,
            fresh_items_24h=fresh_items_24h,
            stale_sources=stale_sources,
            max_story_risk_score=max_story_risk_score,
            operation_mode=operation_mode(
                max_story_risk_score,
                critical_stories,
                high_risk_entities,
            ),
        ),
        risk_queue=await load_risk_queue(session, limit=limit),
        entity_pulse=await load_entity_pulse(session, limit=limit),
        timeline=await load_timeline(session, limit=limit),
        source_health=await load_source_health(
            session,
            limit=limit,
            stale_threshold=stale_threshold,
        ),
    )
