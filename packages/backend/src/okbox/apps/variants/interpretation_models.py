"""Clinical interpretation models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from okbox.core.database import Base


class InterpretationStatus(str, enum.Enum):
    """Interpretation workflow status."""

    UNINTERPRETED = "uninterpreted"
    INTERPRETED = "interpreted"
    REVIEWED = "reviewed"


class Pathogenicity(str, enum.Enum):
    """ACMG pathogenicity classification."""

    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    VUS = "vus"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"


class VariantInterpretation(Base):
    """Clinical interpretation for a variant."""

    __tablename__ = "variant_interpretations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("variants.id"), nullable=False, index=True
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id"), nullable=False, index=True
    )

    # Classification
    pathogenicity: Mapped[Pathogenicity] = mapped_column(
        Enum(Pathogenicity), nullable=False
    )
    include_in_report: Mapped[bool] = mapped_column(Boolean, default=False)

    # Interpretation content
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Workflow status
    status: Mapped[InterpretationStatus] = mapped_column(
        Enum(InterpretationStatus), default=InterpretationStatus.UNINTERPRETED
    )

    # Who and when
    interpreted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    interpreted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InterpretationHistory(Base):
    """History of interpretation changes for audit trail."""

    __tablename__ = "interpretation_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    interpretation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("variant_interpretations.id"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("variants.id"), nullable=False
    )

    # What changed
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "classify", "review"
    old_pathogenicity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_pathogenicity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    old_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Who and when
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
