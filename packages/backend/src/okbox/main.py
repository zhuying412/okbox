"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from okbox.core.config import settings
from okbox.core.exceptions import AppException, app_exception_handler, unhandled_exception_handler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.app_log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="OKBox NGS Data Analysis Platform",
        docs_url="/api/docs" if settings.app_env == "development" else None,
        redoc_url="/api/redoc" if settings.app_env == "development" else None,
        debug=settings.debug,
    )

    # Exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Register routes (before middleware, so health check is available)
    _register_routes(app)

    # Middleware (order matters: last added = first executed)
    # Only add AuditMiddleware if database is configured
    from okbox.middleware.audit import AuditMiddleware

    app.add_middleware(AuditMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


def _register_routes(app: FastAPI) -> None:
    """Register all API routes."""
    from okbox.apps.health import router as health_router

    app.include_router(health_router, prefix="/api/v1")


app = create_app()
