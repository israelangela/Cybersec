from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.db.session import get_session
from cybersec_api.models.story import Story
from cybersec_api.schemas.story import (
    StoryDetailRead,
    StoryItemRead,
    StoryRead,
    StoryStatsRead,
    StorySyncResultRead,
)
from cybersec_api.stories.service import (
    count_high_risk_stories,
    count_stories,
    count_story_items,
    get_story,
    list_stories,
    sync_stories,
)

router = APIRouter(prefix="/stories", tags=["stories"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
StoryLimit = Annotated[int, Query(ge=1, le=500)]
StoryOffset = Annotated[int, Query(ge=0)]
StorySearch = Annotated[str | None, Query(min_length=2, max_length=120)]
StoryMinScore = Annotated[int | None, Query(ge=1, le=100)]
StoryThreshold = Annotated[float, Query(ge=0.1, le=0.95)]


def story_to_detail(story: Story) -> StoryDetailRead:
    story_read = StoryRead.model_validate(story)
    return StoryDetailRead(
        **story_read.model_dump(),
        items=[
            StoryItemRead(
                item_id=story_item.item_id,
                relevance_score=story_item.relevance_score,
                created_at=story_item.created_at,
                item=story_item.item,
            )
            for story_item in sorted(
                story.story_items,
                key=lambda item: item.relevance_score,
                reverse=True,
            )
        ],
    )


@router.post("/sync", response_model=StorySyncResultRead)
async def sync_story_clusters(
    session: DatabaseSession,
    limit: StoryLimit = 500,
    similarity_threshold: StoryThreshold = 0.68,
) -> StorySyncResultRead:
    return await sync_stories(
        session,
        limit=limit,
        similarity_threshold=similarity_threshold,
    )


@router.get("", response_model=list[StoryRead])
async def read_stories(
    session: DatabaseSession,
    severity: str | None = None,
    min_score: StoryMinScore = None,
    search: StorySearch = None,
    limit: StoryLimit = 50,
    offset: StoryOffset = 0,
) -> list[StoryRead]:
    return await list_stories(
        session,
        severity=severity,
        min_score=min_score,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=StoryStatsRead)
async def read_story_stats(session: DatabaseSession) -> StoryStatsRead:
    top_stories = await list_stories(session, limit=5)
    return StoryStatsRead(
        total_stories=await count_stories(session),
        high_risk_stories=await count_high_risk_stories(session),
        linked_items=await count_story_items(session),
        top_stories=[StoryRead.model_validate(story) for story in top_stories],
    )


@router.get("/{story_id}", response_model=StoryDetailRead)
async def read_story(story_id: UUID, session: DatabaseSession) -> StoryDetailRead:
    story = await get_story(session, story_id)

    if story is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")

    return story_to_detail(story)
