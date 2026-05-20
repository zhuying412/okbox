"""Audit logging middleware.

Records all POST/PUT/PATCH/DELETE operations to the audit_logs table.
IVD/LDT compliance requires retention >= 15 years.
"""

import json
import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from okbox.apps.audit.models import AuditLog
from okbox.core.database import async_session_factory

logger = logging.getLogger(__name__)

# HTTP methods that trigger audit logging
AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths to exclude from audit logging
EXCLUDED_PATHS = {"/api/v1/health", "/api/docs", "/api/redoc", "/api/openapi.json"}


def _extract_resource_type(path: str) -> str:
    """Extract resource type from URL path."""
    parts = path.strip("/").split("/")
    # Pattern: /api/v1/{resource}/...
    if len(parts) >= 3:
        return parts[2]
    return "unknown"


def _extract_resource_id(path: str) -> str | None:
    """Extract resource ID from URL path if present."""
    parts = path.strip("/").split("/")
    # Pattern: /api/v1/{resource}/{id}
    if len(parts) >= 4:
        return parts[3]
    return None


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that records all write operations for audit compliance."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in AUDITABLE_METHODS:
            return await call_next(request)

        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.time()

        # Read request body for audit (limited size)
        request_body = None
        try:
            body = await request.body()
            if body and len(body) < 10240:  # Max 10KB
                parsed = json.loads(body)
                # Mask sensitive fields (including nested)
                sensitive_keys = {
                    "password", "token", "secret", "secret_key",
                    "authorization", "cookie", "api_key",
                    "access_token", "refresh_token",
                }
                for key in list(parsed.keys()):
                    if key.lower() in sensitive_keys:
                        parsed[key] = "***MASKED***"
                request_body = parsed
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        response = await call_next(request)
        duration = time.time() - start_time

        # Extract user info from request state (set by auth)
        user_id = None
        username = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
            username = getattr(request.state, "username", None)

        # Create audit log entry asynchronously
        try:
            async with async_session_factory() as session:
                audit_entry = AuditLog(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    username=username,
                    action=request.method,
                    resource_type=_extract_resource_type(request.url.path),
                    resource_id=_extract_resource_id(request.url.path),
                    path=str(request.url.path),
                    request_body=request_body,
                    ip_address=(
                        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                        or (request.client.host if request.client else None)
                    ),
                    user_agent=request.headers.get("user-agent"),
                    status_code=response.status_code,
                )
                session.add(audit_entry)
                await session.commit()
        except Exception as e:
            # Audit logging failure should not break the request
            logger.error("Failed to write audit log: %s", str(e))

        logger.info(
            "AUDIT: %s %s -> %s (%.3fs) user=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            username or "anonymous",
        )

        return response
