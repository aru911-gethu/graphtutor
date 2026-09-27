import pytest
from unittest.mock import AsyncMock
from thinknx.ingest.router import IngestionRouter


@pytest.mark.asyncio
async def test_ingest_router_dispatch():
    """Verify IngestionRouter routes text and url payloads."""
    router = IngestionRouter()
    router.text_ingestor = AsyncMock()
    router.text_ingestor.extract_concepts.return_value = [{"name": "fastapi"}]

    res = await router.dispatch(user_id="u1", source_type="text", payload={"text": "learning fastapi"})
    assert res["source_type"] == "text"
    assert len(res["concepts"]) == 1
    assert res["concepts"][0]["name"] == "fastapi"
