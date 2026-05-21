"""Audit logging middleware.

Records all POST/PUT/PATCH/DELETE operations to the audit_logs table.
IVD/LDT compliance requires retention >= 15 years.

Uses pure ASGI middleware (not BaseHTTPMiddleware) to avoid known Starlette
streaming response issues that can cause 500 errors on health checks.
"""

import json
import logging
import time
import uuid
from io import BytesIO

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

# HTTP methods that trigger audit logging
AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths to skip entirely (no middleware overhead)
EXCLUDED_PATHS = {"/api/v1/health", "/api/docs", "/api/redoc", "/api/openapi.json"}


def _extract_resource_type(path: str) -> str:
    """Extract resource type from URL path."""
    parts = path.strip("/").split("/")
    if len(parts) >= 3:
        return parts[2]
    return "unknown"


def _extract_resource_id(path: str) -> str | None:
    """Extract resource ID from URL path if present."""
    parts = path.strip("/").split("/")
    if len(parts) >= 4:
        return parts[3]
    return None


class AuditMiddleware:
    """Pure ASGI middleware that records write operations for audit compliance."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")

        # Fast path: skip non-auditable methods and excluded paths entirely
        if method not in AUDITABLE_METHODS or path in EXCLUDED_PATHS:
            await self.app(scope, receive, send)
            return

        # Auditable request - capture body and response status
        start_time = time.time()
        request = Request(scope, receive)

        # Read request body for audit (limited size)
        request_body = None
        body_bytes = BytesIO()
        body_consumed = False

        async def receive_wrapper() -> Message:
            nonlocal body_consumed
            message = await receive()
            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                if body_bytes.tell() < 10240:  # Max 10KB
                    body_bytes.write(chunk)
                body_consumed = True
            return message

        # Capture response status code
        status_code = None

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        # Execute the request
        await self.app(scope, receive_wrapper, send_wrapper)

        duration = time.time() - start_time

        # Parse request body
        if body_consumed:
            raw_body = body_bytes.getvalue()
            if raw_body and len(raw_body) < 10240:
                try:
                    parsed = json.loads(raw_body)
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

        # Extract user info from request state (set by auth middleware)
        user_id = None
        username = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
            username = getattr(request.state, "username", None)

        # Write audit log asynchronously (lazy import to avoid startup issues)
        try:
            from okbox.apps.audit.models import AuditLog
            from okbox.core.database import async_session_factory

            async with async_session_factory() as session:
                audit_entry = AuditLog(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    username=username,
                    action=method,
                    resource_type=_extract_resource_type(path),
                    resource_id=_extract_resource_id(path),
                    path=path,
                    request_body=request_body,
                    ip_address=(
                        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                        or (request.client.host if request.client else None)
                    ),
                    user_agent=request.headers.get("user-agent"),
                    status_code=status_code,
                )
                session.add(audit_entry)
                await session.commit()
        except Exception as e:
            # Audit logging failure should not break the request
            logger.error("Failed to write audit log: %s", str(e))

        logger.info(
            "AUDIT: %s %s -> %s (%.3fs) user=%s",
            method,
            path,
            status_code,
            duration,
            username or "anonymous",
        )
