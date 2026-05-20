"""Statistics API routes."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.core.database import get_db

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/samples/monthly")
async def sample_count_monthly(
    months: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Sample count by month."""
    from okbox.apps.samples.models import Sample

    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
    result = await db.execute(
        select(
            extract("year", Sample.created_at).label("year"),
            extract("month", Sample.created_at).label("month"),
            sa_func.count(Sample.id).label("count"),
        )
        .where(Sample.created_at >= cutoff)
        .group_by("year", "month")
        .order_by("year", "month")
    )
    rows = result.all()
    return {
        "data": [
            {"year": int(r.year), "month": int(r.month), "count": r.count}
            for r in rows
        ]
    }


@router.get("/samples/by-panel")
async def sample_count_by_panel(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Sample count grouped by panel type."""
    from okbox.apps.samples.models import Sample

    result = await db.execute(
        select(Sample.panel_type, sa_func.count(Sample.id).label("count"))
        .group_by(Sample.panel_type)
        .order_by(sa_func.count(Sample.id).desc())
    )
    rows = result.all()
    return {"data": [{"panel": r[0], "count": r[1]} for r in rows]}


@router.get("/tat")
async def turnaround_time(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Turnaround time statistics (from registration to report signed)."""
    from okbox.apps.samples.models import Sample, SampleStatus

    # Get completed samples (signed status)
    result = await db.execute(
        select(Sample)
        .where(Sample.status == SampleStatus.SIGNED)
        .order_by(Sample.created_at.desc())
        .limit(100)
    )
    samples = result.scalars().all()

    tat_values = []
    for s in samples:
        if s.updated_at and s.created_at:
            tat_days = (s.updated_at - s.created_at).total_seconds() / 86400
            tat_values.append(tat_days)

    avg_tat = sum(tat_values) / len(tat_values) if tat_values else 0
    return {
        "average_days": round(avg_tat, 1),
        "min_days": round(min(tat_values), 1) if tat_values else 0,
        "max_days": round(max(tat_values), 1) if tat_values else 0,
        "sample_count": len(tat_values),
    }


@router.get("/variants/distribution")
async def variant_type_distribution(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Variant type distribution."""
    from okbox.apps.variants.models import Variant

    result = await db.execute(
        select(Variant.variant_type, sa_func.count(Variant.id).label("count"))
        .group_by(Variant.variant_type)
    )
    rows = result.all()
    return {"data": [{"type": r[0].value, "count": r[1]} for r in rows]}


@router.get("/pipeline/success-rate")
async def pipeline_success_rate(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Pipeline task success rate."""
    from okbox.apps.pipeline.task_models import PipelineTask, TaskStatus

    total_result = await db.execute(select(sa_func.count(PipelineTask.id)))
    total = total_result.scalar() or 0

    completed_result = await db.execute(
        select(sa_func.count(PipelineTask.id))
        .where(PipelineTask.status == TaskStatus.COMPLETED)
    )
    completed = completed_result.scalar() or 0

    failed_result = await db.execute(
        select(sa_func.count(PipelineTask.id))
        .where(PipelineTask.status == TaskStatus.FAILED)
    )
    failed = failed_result.scalar() or 0

    success_rate = (completed / total * 100) if total > 0 else 0
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "success_rate": round(success_rate, 1),
    }


@router.get("/export")
async def export_statistics(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Export comprehensive statistics report."""
    # Aggregate all statistics
    from okbox.apps.samples.models import Sample
    from okbox.apps.pipeline.task_models import PipelineTask
    from okbox.apps.variants.models import Variant

    sample_count = (await db.execute(select(sa_func.count(Sample.id)))).scalar() or 0
    task_count = (await db.execute(select(sa_func.count(PipelineTask.id)))).scalar() or 0
    variant_count = (await db.execute(select(sa_func.count(Variant.id)))).scalar() or 0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_samples": sample_count,
            "total_tasks": task_count,
            "total_variants": variant_count,
        },
    }
