"""Report API routes."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.reports.models import Report, ReportStatus, ReportTemplate
from okbox.apps.reports.schemas import (
    ReportGenerateRequest,
    ReportResponse,
    TemplateCreateRequest,
    TemplateResponse,
)
from okbox.core.database import get_db
from okbox.core.exceptions import NotFoundException

router = APIRouter(prefix="/reports", tags=["reports"])


# ─── Templates ──────────────────────────────────────────────────

@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    request: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Create a new report template."""
    template = ReportTemplate(
        name=request.name,
        description=request.description,
        html_template=request.html_template,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> list[TemplateResponse]:
    """List all active report templates."""
    result = await db.execute(
        select(ReportTemplate)
        .where(ReportTemplate.is_active == True)  # noqa: E712
        .order_by(ReportTemplate.name)
    )
    templates = result.scalars().all()
    return [TemplateResponse.model_validate(t) for t in templates]


# ─── Reports ───────────────────────────────────────────────────

@router.post("/generate", response_model=ReportResponse, status_code=201)
async def generate_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Generate a new report for a sample.

    The report is generated asynchronously (Celery) and status is updated.
    """
    # Verify template exists
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == request.template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise NotFoundException("Template not found")

    # Check if there's an existing report (increment version)
    existing = await db.execute(
        select(sa_func.max(Report.version))
        .where(Report.sample_id == request.sample_id)
    )
    max_version = existing.scalar() or 0

    report = Report(
        sample_id=request.sample_id,
        template_id=request.template_id,
        title=request.title,
        status=ReportStatus.GENERATING,
        version=max_version + 1,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    # TODO: Dispatch Celery task for async HTML + PDF generation
    # For now, mark as generated placeholder
    report.status = ReportStatus.GENERATED
    report.generated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(report)

    return ReportResponse.model_validate(report)


@router.get("", response_model=dict)
async def list_reports(
    sample_id: uuid.UUID | None = Query(None),
    status: ReportStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List reports with optional filters."""
    stmt = select(Report)
    count_stmt = select(sa_func.count(Report.id))

    if sample_id:
        stmt = stmt.where(Report.sample_id == sample_id)
        count_stmt = count_stmt.where(Report.sample_id == sample_id)
    if status:
        stmt = stmt.where(Report.status == status)
        count_stmt = count_stmt.where(Report.status == status)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(Report.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    reports = list(result.scalars().all())

    return {
        "items": [ReportResponse.model_validate(r) for r in reports],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Get report details."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report not found")
    return ReportResponse.model_validate(report)
