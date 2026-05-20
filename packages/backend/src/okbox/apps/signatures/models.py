"""Electronic signature models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from okbox.core.database import Base


class SignatureRole(str, enum.Enum):
    """Signature role in the approval chain."""

    ANALYST_REVIEW = "analyst_review"  # Initial review by analyst
    DOCTOR_REVIEW = "doctor_review"  # Doctor verification
    DIRECTOR_SIGN = "director_sign"  # Final director signature


class SignatureStatus(str, enum.Enum):
    """Signature status."""

    PENDING = "pending"
    SIGNED = "signed"
    REJECTED = "rejected"


class Signature(Base):
    """Electronic signature record.

    Immutable once signed - hash verification ensures report integrity.
    """

    __tablename__ = "signatures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True
    )
    signer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Signature details
    role: Mapped[SignatureRole] = mapped_column(Enum(SignatureRole), nullable=False)
    status: Mapped[SignatureStatus] = mapped_column(
        Enum(SignatureStatus), default=SignatureStatus.PENDING
    )

    # Signer info captured at sign time
    signer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    signer_qualification: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Integrity
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 of report content
    signature_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Rejection reason
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
