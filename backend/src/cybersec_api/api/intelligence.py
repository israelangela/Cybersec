from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.db.session import get_session
from cybersec_api.intelligence.service import (
    count_entities_by_type,
    count_high_risk_entities,
    count_total_entities,
    count_unique_entities,
    external_references,
    list_entity_aggregates,
    list_entity_items,
    list_entity_stories,
    list_item_entities,
    list_top_risk_entities,
    normalize_entity,
    sync_intelligence_entities,
)
from cybersec_api.schemas.context import CyberEntityContextRead, ExternalReferenceRead
from cybersec_api.schemas.intelligence import (
    CyberEntityAggregateRead,
    CyberEntityRead,
    CyberEntityRiskRead,
    CyberEntityTypeCountRead,
    IntelligenceStatsRead,
    IntelligenceSyncResultRead,
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
EntityLimit = Annotated[int, Query(ge=1, le=500)]
EntityOffset = Annotated[int, Query(ge=0)]
EntitySearch = Annotated[str | None, Query(min_length=2, max_length=120)]
EntityMinScore = Annotated[int | None, Query(ge=1, le=100)]


@router.post("/sync", response_model=IntelligenceSyncResultRead)
async def sync_intelligence(
    session: DatabaseSession,
    limit: EntityLimit = 500,
) -> IntelligenceSyncResultRead:
    return await sync_intelligence_entities(session, limit=limit)


@router.get("/entities", response_model=list[CyberEntityAggregateRead])
async def read_entity_aggregates(
    session: DatabaseSession,
    entity_type: str | None = None,
    severity: str | None = None,
    min_score: EntityMinScore = None,
    search: EntitySearch = None,
    limit: EntityLimit = 50,
    offset: EntityOffset = 0,
) -> list[CyberEntityAggregateRead]:
    rows = await list_entity_aggregates(
        session,
        entity_type=entity_type,
        severity=severity,
        min_score=min_score,
        search=search,
        limit=limit,
        offset=offset,
    )

    return [
        CyberEntityAggregateRead(
            entity_type=entity_type,
            value=value,
            normalized_value=normalized_value,
            occurrences=occurrences,
            max_risk_score=max_risk_score,
            avg_confidence=round(avg_confidence, 2) if avg_confidence is not None else None,
            severity=severity,
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
        )
        for (
            entity_type,
            value,
            normalized_value,
            occurrences,
            max_risk_score,
            avg_confidence,
            severity,
            first_seen_at,
            last_seen_at,
        ) in rows
    ]


@router.get("/entities/context", response_model=CyberEntityContextRead)
async def read_entity_context(
    session: DatabaseSession,
    entity_type: str,
    value: Annotated[str, Query(min_length=1, max_length=255)],
    limit: EntityLimit = 100,
) -> CyberEntityContextRead:
    normalized_value = normalize_entity(entity_type, value)
    aggregate_rows = await list_entity_aggregates(
        session,
        entity_type=entity_type,
        search=normalized_value,
        limit=500,
    )
    entity_row = next(
        (
            row
            for row in aggregate_rows
            if row[0] == entity_type and row[2] == normalized_value
        ),
        None,
    )

    if entity_row is None:
        entity_row = (
            entity_type,
            value,
            normalized_value,
            0,
            0,
            None,
            None,
            None,
            None,
        )

    (
        row_entity_type,
        row_value,
        row_normalized_value,
        occurrences,
        max_risk_score,
        avg_confidence,
        severity,
        first_seen_at,
        last_seen_at,
    ) = entity_row

    return CyberEntityContextRead(
        entity=CyberEntityAggregateRead(
            entity_type=row_entity_type,
            value=row_value,
            normalized_value=row_normalized_value,
            occurrences=occurrences,
            max_risk_score=max_risk_score,
            avg_confidence=round(avg_confidence, 2) if avg_confidence is not None else None,
            severity=severity,
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
        ),
        items=await list_entity_items(
            session,
            entity_type=entity_type,
            normalized_value=normalized_value,
            limit=limit,
        ),
        stories=await list_entity_stories(
            session,
            entity_type=entity_type,
            normalized_value=normalized_value,
        ),
        external_references=[
            ExternalReferenceRead(label=label, url=url)
            for label, url in external_references(entity_type, normalized_value)
        ],
    )


@router.get("/items/{item_id}/entities", response_model=list[CyberEntityRead])
async def read_item_entities(
    item_id: UUID,
    session: DatabaseSession,
) -> list[CyberEntityRead]:
    return await list_item_entities(session, item_id)


@router.get("/stats", response_model=IntelligenceStatsRead)
async def read_intelligence_stats(session: DatabaseSession) -> IntelligenceStatsRead:
    top_risks = await list_top_risk_entities(session)

    return IntelligenceStatsRead(
        total_entities=await count_total_entities(session),
        unique_entities=await count_unique_entities(session),
        high_risk_entities=await count_high_risk_entities(session),
        by_type=[
            CyberEntityTypeCountRead(entity_type=entity_type, count=count)
            for entity_type, count in await count_entities_by_type(session)
        ],
        top_risks=[
            CyberEntityRiskRead(
                entity_type=entity.entity_type,
                value=entity.value,
                normalized_value=entity.normalized_value,
                risk_score=entity.risk_score,
                severity=entity.severity,
                item_id=entity.item_id,
                last_seen_at=entity.last_seen_at,
            )
            for entity in top_risks
        ],
    )
