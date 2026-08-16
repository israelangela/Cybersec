from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersec_api.models.cyber_entity import CyberEntity
from cybersec_api.models.item import Item
from cybersec_api.models.report import Report, ReportItem, ReportStory
from cybersec_api.models.story import Story, StoryItem

SEVERITY_ORDER = {
    "informational": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}


@dataclass(slots=True)
class ReportBuildInput:
    title: str | None
    report_type: str
    severity: str | None
    min_score: int | None
    story_ids: list[UUID]
    limit: int


def report_title(build_input: ReportBuildInput, stories: list[Story]) -> str:
    if build_input.title:
        return build_input.title

    if not stories:
        return "CyberSec Intelligence Report"

    top_story = max(stories, key=lambda story: story.risk_score)
    return f"CyberSec {build_input.report_type.title()} Report - {top_story.title}"


def report_period(items: list[Item]) -> tuple[datetime | None, datetime | None]:
    values = [
        item.published_at or item.collected_at
        for item in items
        if item.published_at is not None or item.collected_at is not None
    ]

    if not values:
        return None, None

    return min(values), max(values)


def story_items(stories: list[Story]) -> list[Item]:
    seen: set[UUID] = set()
    items: list[Item] = []

    for story in stories:
        for story_item in sorted(
            story.story_items,
            key=lambda link: link.relevance_score,
            reverse=True,
        ):
            item = story_item.item

            if item is None or item.id in seen:
                continue

            seen.add(item.id)
            items.append(item)

    return items


def report_entities(items: list[Item]) -> list[CyberEntity]:
    seen: set[tuple[str, str]] = set()
    entities: list[CyberEntity] = []

    for item in items:
        for entity in sorted(item.cyber_entities, key=lambda value: value.risk_score, reverse=True):
            key = (entity.entity_type, entity.normalized_value)

            if key in seen:
                continue

            seen.add(key)
            entities.append(entity)

    return entities


def strongest_severity(stories: list[Story], entities: list[CyberEntity]) -> str | None:
    severities = [story.severity for story in stories if story.severity]
    severities.extend(entity.severity for entity in entities if entity.severity)

    if not severities:
        return None

    return max(severities, key=lambda severity: SEVERITY_ORDER.get(severity, 0))


def source_count(items: list[Item]) -> int:
    return len({item.source_id for item in items})


def report_summary(stories: list[Story], entities: list[CyberEntity]) -> str:
    if not stories:
        return "No reportable stories matched the selected filters."

    top_story = max(stories, key=lambda story: story.risk_score)
    critical_count = sum(1 for story in stories if story.risk_score >= 85)
    high_count = sum(1 for story in stories if story.risk_score >= 70)
    entity_values = ", ".join(entity.normalized_value for entity in entities[:6])

    return (
        f"{len(stories)} stories were selected. Highest risk is {top_story.risk_score} "
        f"from '{top_story.title}'. Critical stories: {critical_count}. "
        f"High-risk stories: {high_count}. Key entities: {entity_values or 'none'}."
    )


def citation_lines(items: list[Item]) -> list[str]:
    lines = []

    for index, item in enumerate(items, 1):
        title = item.normalized_title or item.title
        source = item.source_name or "Unknown source"
        lines.append(f"[R{index}] {title} - {source} - {item.url}")

    return lines


def build_markdown(
    *,
    title: str,
    summary: str,
    stories: list[Story],
    items: list[Item],
    entities: list[CyberEntity],
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Executive Summary",
        "",
        summary,
        "",
        "## Risk Stories",
        "",
    ]

    if not stories:
        lines.append("No stories matched the selected filters.")
    else:
        for story in stories:
            lines.extend(
                [
                    f"### {story.title}",
                    "",
                    f"- Risk: {story.risk_score}",
                    f"- Severity: {story.severity or 'unknown'}",
                    f"- News items: {story.item_count}",
                    f"- Entities: {story.entity_count}",
                    f"- Summary: {story.summary or 'No summary'}",
                    "",
                ]
            )

    lines.extend(["## Key Entities", ""])
    entity_counts = Counter(entity.entity_type for entity in entities)

    if entities:
        lines.extend(
            f"- {entity.normalized_value} ({entity.entity_type}, risk {entity.risk_score})"
            for entity in entities[:20]
        )
        lines.append("")
        lines.append(
            "Entity distribution: "
            + ", ".join(f"{entity_type}: {count}" for entity_type, count in entity_counts.items())
        )
    else:
        lines.append("No cyber entities were linked to this report.")

    lines.extend(["", "## Evidence", ""])
    lines.extend(citation_lines(items) or ["No cited source items."])
    lines.extend(
        [
            "",
            "## Analyst Notes",
            "",
            "This report is generated from CyberSec derived intelligence. Review cited source "
            "items before taking operational action.",
        ]
    )

    return "\n".join(lines)


async def load_report_stories(session: AsyncSession, build_input: ReportBuildInput) -> list[Story]:
    statement = select(Story).options(
        selectinload(Story.story_items)
        .selectinload(StoryItem.item)
        .selectinload(Item.source),
        selectinload(Story.story_items)
        .selectinload(StoryItem.item)
        .selectinload(Item.enrichment),
        selectinload(Story.story_items)
        .selectinload(StoryItem.item)
        .selectinload(Item.cyber_entities),
    )

    if build_input.story_ids:
        statement = statement.where(Story.id.in_(build_input.story_ids))

    if build_input.severity is not None:
        statement = statement.where(Story.severity == build_input.severity)

    if build_input.min_score is not None:
        statement = statement.where(Story.risk_score >= build_input.min_score)

    statement = statement.order_by(Story.risk_score.desc(), Story.last_seen_at.desc().nullslast())

    if not build_input.story_ids:
        statement = statement.limit(build_input.limit)

    return list((await session.scalars(statement)).unique().all())


async def create_report(
    session: AsyncSession,
    build_input: ReportBuildInput,
) -> Report:
    stories = await load_report_stories(session, build_input)
    items = story_items(stories)
    entities = report_entities(items)
    title = report_title(build_input, stories)
    summary = report_summary(stories, entities)
    period_start, period_end = report_period(items)
    body_markdown = build_markdown(
        title=title,
        summary=summary,
        stories=stories,
        items=items,
        entities=entities,
    )
    report = Report(
        title=title,
        report_type=build_input.report_type,
        status="draft",
        summary=summary,
        body_markdown=body_markdown,
        severity=strongest_severity(stories, entities),
        risk_score=max((story.risk_score for story in stories), default=0),
        story_count=len(stories),
        item_count=len(items),
        entity_count=len(entities),
        source_count=source_count(items),
        period_start=period_start,
        period_end=period_end,
        filters={
            "severity": build_input.severity,
            "min_score": build_input.min_score,
            "story_ids": [str(story_id) for story_id in build_input.story_ids],
            "limit": build_input.limit,
        },
        created_at=datetime.now(UTC),
    )
    session.add(report)
    await session.flush()

    for position, story in enumerate(stories, 1):
        session.add(ReportStory(report_id=report.id, story_id=story.id, position=position))

    for index, item in enumerate(items, 1):
        session.add(ReportItem(report_id=report.id, item_id=item.id, citation_id=f"R{index}"))

    await session.commit()
    return await get_report(session, report.id) or report


async def list_reports(
    session: AsyncSession,
    *,
    report_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Report]:
    statement = select(Report)

    if report_type is not None:
        statement = statement.where(Report.report_type == report_type)

    if status is not None:
        statement = statement.where(Report.status == status)

    statement = statement.order_by(Report.created_at.desc()).offset(offset).limit(limit)
    return list((await session.scalars(statement)).all())


async def get_report(session: AsyncSession, report_id: UUID) -> Report | None:
    statement = (
        select(Report)
        .options(
            selectinload(Report.report_stories).selectinload(ReportStory.story),
            selectinload(Report.report_items)
            .selectinload(ReportItem.item)
            .selectinload(Item.source),
            selectinload(Report.report_items)
            .selectinload(ReportItem.item)
            .selectinload(Item.enrichment),
        )
        .where(Report.id == report_id)
    )
    return await session.scalar(statement)


async def delete_report(session: AsyncSession, report_id: UUID) -> bool:
    result = await session.execute(delete(Report).where(Report.id == report_id))
    await session.commit()
    return bool(result.rowcount)
