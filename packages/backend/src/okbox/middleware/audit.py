"""Audit logging middleware (framework placeholder).

This middleware will record all write operations (POST/PUT/PATCH/DELETE)
for compliance purposes. Full implementation in Issue #30.
"""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

# HTTP methods that trigger audit logging
AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs write operations for audit compliance."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in AUDITABLE_METHODS:
            start_time = time.time()
            response = await call_next(request)
            duration = time.time() - start_time

            # Placeholder: full audit logging implementation in Issue #30
            logger.info(
                "AUDIT: %s %s -> %s (%.3fs)",
                request.method,
                request.url.path,
                response.status_code,
                duration,
            )
            return response

        return await call_next(request)
