"""Audit log schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    username: str | None
    action: str
    resource_type: str
    resource_id: str | None
    path: str
    changes: dict | None
    ip_address: str | None
    status_code: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogQuery(BaseModel):
    """Audit log query parameters."""

    user_id: uuid.UUID | None = None
    action: str | None = None
    resource_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    page: int = 1
    page_size: int = 50
