"""QC business logic - parsing, evaluation, alerts."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.qc.models import QCMetrics, QCStatus, QCThreshold
from okbox.apps.qc.schemas import QCMetricsCreateRequest


async def evaluate_qc_status(db: AsyncSession, metrics: QCMetrics) -> QCStatus:
    """Evaluate QC metrics against configured thresholds.

    Returns the worst status among all metrics.
    """
    result = await db.execute(select(QCThreshold).where(QCThreshold.is_active == True))  # noqa: E712
    thresholds = result.scalars().all()

    worst_status = QCStatus.PASS

    for threshold in thresholds:
        metric_value = getattr(metrics, threshold.metric_name, None)
        if metric_value is None:
            continue

        status = _check_threshold(metric_value, threshold)
        if status == QCStatus.FAIL:
            worst_status = QCStatus.FAIL
            break
        elif status == QCStatus.WARN and worst_status == QCStatus.PASS:
            worst_status = QCStatus.WARN

    return worst_status


def _check_threshold(value: float, threshold: QCThreshold) -> QCStatus:
    """Check a single metric against its threshold."""
    if threshold.direction == "gte":
        # Higher is better (e.g., coverage, Q30)
        if threshold.fail_threshold is not None and value < threshold.fail_threshold:
            return QCStatus.FAIL
        if threshold.warn_threshold is not None and value < threshold.warn_threshold:
            return QCStatus.WARN
    else:
        # Lower is better (e.g., duplication rate)
        if threshold.fail_threshold is not None and value > threshold.fail_threshold:
            return QCStatus.FAIL
        if threshold.warn_threshold is not None and value > threshold.warn_threshold:
            return QCStatus.WARN
    return QCStatus.PASS


async def create_qc_metrics(
    db: AsyncSession, request: QCMetricsCreateRequest
) -> QCMetrics:
    """Create QC metrics and evaluate status."""
    metrics = QCMetrics(**request.model_dump())
    db.add(metrics)
    await db.flush()

    # Evaluate against thresholds
    status = await evaluate_qc_status(db, metrics)
    metrics.status = status
    metrics.is_alert = status == QCStatus.FAIL

    await db.flush()
    await db.refresh(metrics)
    return metrics


async def get_sample_qc(db: AsyncSession, sample_id: uuid.UUID) -> list[QCMetrics]:
    """Get all QC metrics for a sample."""
    result = await db.execute(
        select(QCMetrics)
        .where(QCMetrics.sample_id == sample_id)
        .order_by(QCMetrics.created_at.desc())
    )
    return list(result.scalars().all())
