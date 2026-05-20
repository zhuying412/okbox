"""Report preview and export API routes."""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.reports.models import Report
from okbox.core.database import get_db
from okbox.core.exceptions import NotFoundException

router = APIRouter(prefix="/reports", tags=["reports-export"])


@router.get("/{report_id}/preview", response_class=HTMLResponse)
async def preview_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Web preview of report (HTML rendering)."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report not found")
    if not report.html_content:
        raise NotFoundException("Report HTML content not available")
    return HTMLResponse(content=report.html_content)


@router.get("/{report_id}/download/pdf")
async def download_pdf(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Download report as PDF."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report not found")
    if not report.pdf_path:
        raise NotFoundException("PDF not generated yet")

    import os
    if not os.path.exists(report.pdf_path):
        raise NotFoundException("PDF file not found on disk")

    def iterfile():
        with open(report.pdf_path, "rb") as f:
            yield from f

    return StreamingResponse(
        iterfile(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report_{report_id}.pdf"'},
    )


@router.get("/{report_id}/export/json")
async def export_json(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Export report data as structured JSON."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report not found")

    return {
        "report_id": str(report.id),
        "sample_id": str(report.sample_id),
        "title": report.title,
        "version": report.version,
        "status": report.status.value,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        # Note: in production, include variants + interpretations data
    }


@router.get("/{report_id}/export/csv")
async def export_csv(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export report variants as CSV."""
    import csv
    import io

    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report not found")

    # Generate CSV content (placeholder - in production queries variant data)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Gene", "Chromosome", "Position", "REF", "ALT", "VAF", "Pathogenicity"])
    # In production: query variants for this sample and write rows

    csv_content = output.getvalue()
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="report_{report_id}.csv"'},
    )
