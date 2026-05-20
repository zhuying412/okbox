"""QC data models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from okbox.core.database import Base


class QCStatus(str, enum.Enum):
    """QC result status."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class QCMetrics(Base):
    """QC metrics for a sample/task - parsed from pipeline output."""

    __tablename__ = "qc_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipeline_tasks.id"), nullable=True
    )

    # Core QC metrics
    total_reads: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mapped_reads: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mapping_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_depth: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_10x: Mapped[float | None] = mapped_column(Float, nullable=True)  # % at >= 10x
    coverage_30x: Mapped[float | None] = mapped_column(Float, nullable=True)  # % at >= 30x
    coverage_100x: Mapped[float | None] = mapped_column(Float, nullable=True)  # % at >= 100x
    q30_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    duplication_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    insert_size_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    gc_content: Mapped[float | None] = mapped_column(Float, nullable=True)
    on_target_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    uniformity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Overall QC status
    status: Mapped[QCStatus] = mapped_column(
        Enum(QCStatus), nullable=False, default=QCStatus.PASS
    )
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False)

    # Extra metrics as JSON
    extra_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QCThreshold(Base):
    """Configurable QC thresholds for pass/warn/fail determination."""

    __tablename__ = "qc_thresholds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    metric_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    warn_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    fail_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    direction: Mapped[str] = mapped_column(
        String(10), default="gte"  # "gte" = greater is better, "lte" = lower is better
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
