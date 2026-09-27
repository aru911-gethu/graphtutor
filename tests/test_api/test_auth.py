import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dev_token_generation(client: AsyncClient):
    """Verify development JWT token generation."""
    response = await client.post("/api/auth/dev-token")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "aru91190@gmail.com"


@pytest.mark.asyncio
async def test_auth_me_with_token(client: AsyncClient):
    """Verify /api/auth/me returns authenticated user with valid token."""
    # 1. Obtain token
    token_resp = await client.post("/api/auth/dev-token")
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]

    # 2. Call /api/auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = await client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["email"] == "aru91190@gmail.com"
    assert "platform" in user_data


@pytest.mark.asyncio
async def test_auth_me_unauthorized(client: AsyncClient):
    """Verify /api/auth/me rejects missing or invalid token."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
