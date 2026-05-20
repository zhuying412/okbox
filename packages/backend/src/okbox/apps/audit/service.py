"""Audit log service - query operations."""

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.audit.models import AuditLog
from okbox.apps.audit.schemas import AuditLogQuery


async def query_audit_logs(
    db: AsyncSession, query: AuditLogQuery
) -> tuple[list[AuditLog], int]:
    """Query audit logs with filters and pagination."""
    stmt = select(AuditLog)
    count_stmt = select(sa_func.count(AuditLog.id))

    # Apply filters
    if query.user_id:
        stmt = stmt.where(AuditLog.user_id == query.user_id)
        count_stmt = count_stmt.where(AuditLog.user_id == query.user_id)
    if query.action:
        stmt = stmt.where(AuditLog.action == query.action)
        count_stmt = count_stmt.where(AuditLog.action == query.action)
    if query.resource_type:
        stmt = stmt.where(AuditLog.resource_type == query.resource_type)
        count_stmt = count_stmt.where(AuditLog.resource_type == query.resource_type)
    if query.start_time:
        stmt = stmt.where(AuditLog.created_at >= query.start_time)
        count_stmt = count_stmt.where(AuditLog.created_at >= query.start_time)
    if query.end_time:
        stmt = stmt.where(AuditLog.created_at <= query.end_time)
        count_stmt = count_stmt.where(AuditLog.created_at <= query.end_time)

    # Get total count
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (query.page - 1) * query.page_size
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(query.page_size)

    result = await db.execute(stmt)
    logs = list(result.scalars().all())

    return logs, total
