import pytest
from unittest.mock import AsyncMock
from thinknx.channels.router import NormalizedMessage, ChannelRouter


@pytest.mark.asyncio
async def test_channel_router_dispatch():
    """Verify ChannelRouter correctly routes messages based on media type."""
    mock_engine = AsyncMock()
    mock_ingest = AsyncMock()
    mock_ingest.process_image.return_value = {"description": "Diagram"}

    router = ChannelRouter(learning_engine=mock_engine, ingestion_router=mock_ingest)

    # Photo message
    msg = NormalizedMessage(
        user_id="telegram:123",
        platform="telegram",
        media_type="photo",
        media_bytes=b"fake_image_bytes"
    )

    res = await router.route_message(msg)
    assert res["description"] == "Diagram"
    mock_ingest.process_image.assert_called_once_with("telegram:123", b"fake_image_bytes")
