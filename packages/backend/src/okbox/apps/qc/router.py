"""QC API routes."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.qc.models import QCMetrics, QCThreshold
from okbox.apps.qc.schemas import (
    QCMetricsCreateRequest,
    QCMetricsResponse,
    QCThresholdResponse,
    QCThresholdUpdateRequest,
)
from okbox.apps.qc.service import create_qc_metrics, get_sample_qc
from okbox.core.database import get_db
from okbox.core.exceptions import NotFoundException

router = APIRouter(prefix="/qc", tags=["qc"])


@router.post("/metrics", response_model=QCMetricsResponse, status_code=201)
async def create_metrics(
    request: QCMetricsCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> QCMetricsResponse:
    """Create QC metrics (typically called by pipeline completion hook)."""
    metrics = await create_qc_metrics(db, request)
    return QCMetricsResponse.model_validate(metrics)


@router.get("/sample/{sample_id}", response_model=list[QCMetricsResponse])
async def get_sample_metrics(
    sample_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[QCMetricsResponse]:
    """Get QC metrics for a sample."""
    metrics = await get_sample_qc(db, sample_id)
    return [QCMetricsResponse.model_validate(m) for m in metrics]


@router.get("/alerts", response_model=list[QCMetricsResponse])
async def get_qc_alerts(
    db: AsyncSession = Depends(get_db),
) -> list[QCMetricsResponse]:
    """Get all samples with QC alerts (failed)."""
    result = await db.execute(
        select(QCMetrics)
        .where(QCMetrics.is_alert == True)  # noqa: E712
        .order_by(QCMetrics.created_at.desc())
        .limit(100)
    )
    metrics = result.scalars().all()
    return [QCMetricsResponse.model_validate(m) for m in metrics]


@router.get("/thresholds", response_model=list[QCThresholdResponse])
async def get_thresholds(
    db: AsyncSession = Depends(get_db),
) -> list[QCThresholdResponse]:
    """Get all QC threshold configurations."""
    result = await db.execute(select(QCThreshold).order_by(QCThreshold.metric_name))
    thresholds = result.scalars().all()
    return [QCThresholdResponse.model_validate(t) for t in thresholds]


@router.patch("/thresholds/{threshold_id}", response_model=QCThresholdResponse)
async def update_threshold(
    threshold_id: uuid.UUID,
    request: QCThresholdUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> QCThresholdResponse:
    """Update a QC threshold configuration."""
    result = await db.execute(select(QCThreshold).where(QCThreshold.id == threshold_id))
    threshold = result.scalar_one_or_none()
    if not threshold:
        raise NotFoundException("Threshold not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(threshold, key, value)

    await db.flush()
    await db.refresh(threshold)
    return QCThresholdResponse.model_validate(threshold)
