"""Test health check endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from okbox.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Health check returns 200 with ok status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "okbox-backend"
