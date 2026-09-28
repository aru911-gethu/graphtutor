import pytest
from unittest.mock import patch
from httpx import AsyncClient
from tests.conftest import MockNeo4jSession


@pytest.mark.asyncio
async def test_get_progress_endpoint(client: AsyncClient, mock_neo4j_driver):
    """Verify progress endpoint returns user stats."""
    with patch("thinknx.api.progress.get_driver", return_value=mock_neo4j_driver):
        resp = await client.get("/api/progress/telegram:123456")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "telegram:123456"
        assert "stats" in data
        assert data["stats"]["totalConcepts"] == 12


@pytest.mark.asyncio
async def test_lesson_html_view(client: AsyncClient, mock_neo4j_driver):
    """Verify that polymorphic HTML lesson view renders correctly for webapp."""
    with patch("thinknx.api.lesson.get_driver", return_value=mock_neo4j_driver):
        resp = await client.get("/lesson/transformers?uid=telegram:123456&theme=code")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Transformers" in resp.text
