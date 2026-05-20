"""Sample data models."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from okbox.core.database import Base


class SampleStatus(str, enum.Enum):
    """Sample workflow status."""

    REGISTERED = "registered"
    ANALYZING = "analyzing"
    INTERPRETED = "interpreted"
    REPORTED = "reported"
    SIGNED = "signed"


class SampleType(str, enum.Enum):
    """Biological sample type."""

    BLOOD = "blood"
    TISSUE = "tissue"
    FFPE = "ffpe"
    CTDNA = "ctDNA"
    BONE_MARROW = "bone_marrow"
    OTHER = "other"


class Sample(Base):
    """Sample entity - core of the analysis workflow."""

    __tablename__ = "samples"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sample_no: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    patient_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    patient_id_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sample_type: Mapped[SampleType] = mapped_column(Enum(SampleType), nullable=False)
    panel_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[SampleStatus] = mapped_column(
        Enum(SampleStatus), nullable=False, default=SampleStatus.REGISTERED, index=True
    )
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign keys
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
