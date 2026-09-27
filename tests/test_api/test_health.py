import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Verify that /health responds with valid structure."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["app"] == "thinknx"
    assert "version" in data
    assert "neo4j" in data
    assert "redis" in data


@pytest.mark.asyncio
async def test_root_redirect(client: AsyncClient):
    """Verify that root redirects to OpenAPI docs."""
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
