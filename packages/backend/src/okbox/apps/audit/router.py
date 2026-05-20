"""Audit log API routes."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.audit.schemas import AuditLogQuery, AuditLogResponse
from okbox.apps.audit.service import query_audit_logs
from okbox.core.database import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=dict)
async def get_audit_logs(
    user_id: UUID | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Query audit logs with filters and pagination.

    Restricted to admin users only - audit logs contain sensitive operational data.
    """
    query = AuditLogQuery(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    logs, total = await query_audit_logs(db, query)
    return {
        "items": [AuditLogResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
