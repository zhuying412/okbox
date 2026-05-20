"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint returns 200 when the service is running."""
    return {"status": "ok", "service": "okbox-backend"}
