"""Audit log model - INSERT only, no UPDATE/DELETE allowed."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from okbox.core.database import Base


class AuditLog(Base):
    """Immutable audit log entry.

    Database-level constraints should prevent UPDATE and DELETE:
    CREATE RULE audit_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
    CREATE RULE audit_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Who performed the action
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # What was done
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # POST/PUT/PATCH/DELETE
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "samples"
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Change details
    changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    request_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_code: Mapped[int | None] = mapped_column(nullable=True)

    # When
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
