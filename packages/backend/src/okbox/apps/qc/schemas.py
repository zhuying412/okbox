"""QC schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from okbox.apps.qc.models import QCStatus


class QCMetricsResponse(BaseModel):
    """QC metrics response."""

    id: uuid.UUID
    sample_id: uuid.UUID
    task_id: uuid.UUID | None
    total_reads: int | None
    mapped_reads: int | None
    mapping_rate: float | None
    mean_depth: float | None
    coverage_10x: float | None
    coverage_30x: float | None
    coverage_100x: float | None
    q30_rate: float | None
    duplication_rate: float | None
    insert_size_mean: float | None
    gc_content: float | None
    on_target_rate: float | None
    uniformity: float | None
    status: QCStatus
    is_alert: bool
    extra_metrics: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class QCMetricsCreateRequest(BaseModel):
    """Create QC metrics (from pipeline output parser)."""

    sample_id: uuid.UUID
    task_id: uuid.UUID | None = None
    total_reads: int | None = None
    mapped_reads: int | None = None
    mapping_rate: float | None = None
    mean_depth: float | None = None
    coverage_10x: float | None = None
    coverage_30x: float | None = None
    coverage_100x: float | None = None
    q30_rate: float | None = None
    duplication_rate: float | None = None
    insert_size_mean: float | None = None
    gc_content: float | None = None
    on_target_rate: float | None = None
    uniformity: float | None = None
    extra_metrics: dict | None = None


class QCThresholdResponse(BaseModel):
    """QC threshold config response."""

    id: uuid.UUID
    metric_name: str
    display_name: str
    warn_threshold: float | None
    fail_threshold: float | None
    direction: str
    is_active: bool

    class Config:
        from_attributes = True


class QCThresholdUpdateRequest(BaseModel):
    """Update QC threshold."""

    warn_threshold: float | None = None
    fail_threshold: float | None = None
    is_active: bool | None = None
