import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    """Verify that the API is up and running."""
    async with AsyncClient(base_url="http://test") as ac:
        ac.app = app
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify the root metadata endpoint."""
    async with AsyncClient(base_url="http://test") as ac:
        ac.app = app
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Boxing Training API"
    assert "version" in data

