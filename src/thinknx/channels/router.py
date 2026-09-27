from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from datetime import datetime, timezone


@dataclass
class NormalizedMessage:
    """Normalized cross-channel message abstraction."""
    user_id: str
    platform: str
    text: Optional[str] = None
    media_type: Optional[str] = None  # "photo", "voice", "document", "callback"
    media_bytes: Optional[bytes] = None
    callback_data: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChannelRouter:
    """Routes normalized inbound messages to learning engine or ingestion pipelines."""

    def __init__(self, learning_engine, ingestion_router):
        self.engine = learning_engine
        self.ingest = ingestion_router

    async def route_message(self, msg: NormalizedMessage) -> Dict[str, Any]:
        """Dispatch message based on media type or content."""
        if msg.media_type == "photo" and msg.media_bytes:
            return await self.ingest.process_image(msg.user_id, msg.media_bytes)
        elif msg.media_type == "voice" and msg.media_bytes:
            return await self.ingest.process_audio(msg.user_id, msg.media_bytes)
        elif msg.text:
            return {"type": "text", "content": msg.text}
        return {"type": "unknown"}
