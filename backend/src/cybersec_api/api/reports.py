from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.db.session import get_session
from cybersec_api.models.report import Report
from cybersec_api.reports.service import (
    ReportBuildInput,
    create_report,
    delete_report,
    get_report,
    list_reports,
)
from cybersec_api.schemas.report import (
    ReportDetailRead,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportItemRead,
    ReportRead,
    ReportStoryRead,
)

router = APIRouter(prefix="/reports", tags=["reports"])
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
ReportLimit = Annotated[int, Query(ge=1, le=100)]
ReportOffset = Annotated[int, Query(ge=0)]


def report_to_detail(report: Report) -> ReportDetailRead:
    report_read = ReportRead.model_validate(report)
    return ReportDetailRead(
        **report_read.model_dump(),
        body_markdown=report.body_markdown,
        stories=[
            ReportStoryRead(
                story_id=report_story.story_id,
                position=report_story.position,
                story=report_story.story,
            )
            for report_story in sorted(report.report_stories, key=lambda item: item.position)
        ],
        items=[
            ReportItemRead(
                item_id=report_item.item_id,
                citation_id=report_item.citation_id,
                item=report_item.item,
            )
            for report_item in sorted(report.report_items, key=lambda item: item.citation_id)
        ],
    )


@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_report(
    payload: ReportGenerateRequest,
    session: DatabaseSession,
) -> ReportGenerateResponse:
    report = await create_report(
        session,
        ReportBuildInput(
            title=payload.title,
            report_type=payload.report_type,
            severity=payload.severity,
            min_score=payload.min_score,
            story_ids=payload.story_ids,
            limit=payload.limit,
        ),
    )
    return ReportGenerateResponse(status="created", report=report_to_detail(report))


@router.get("", response_model=list[ReportRead])
async def read_reports(
    session: DatabaseSession,
    report_type: str | None = None,
    status: str | None = None,
    limit: ReportLimit = 50,
    offset: ReportOffset = 0,
) -> list[ReportRead]:
    return await list_reports(
        session,
        report_type=report_type,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_id}", response_model=ReportDetailRead)
async def read_report(report_id: UUID, session: DatabaseSession) -> ReportDetailRead:
    report = await get_report(session, report_id)

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return report_to_detail(report)


@router.get("/{report_id}/markdown")
async def read_report_markdown(report_id: UUID, session: DatabaseSession) -> Response:
    report = await get_report(session, report_id)

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return Response(
        content=report.body_markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{report.id}.md"'},
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_report(report_id: UUID, session: DatabaseSession) -> Response:
    deleted = await delete_report(session, report_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
