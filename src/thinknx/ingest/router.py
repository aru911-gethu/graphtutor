from typing import Dict, Any, Optional
import structlog

from thinknx.ingest.text import TextIngestor
from thinknx.ingest.vision import VisionIngestor
from thinknx.ingest.audio import AudioIngestor
from thinknx.ingest.github import GitHubIngestor
from thinknx.ingest.feeds import FeedIngestor

logger = structlog.get_logger(__name__)


class IngestionRouter:
    """Dispatches diverse input formats to specialized multimodal ingestion pipelines."""

    def __init__(
        self,
        text_ingestor: Optional[TextIngestor] = None,
        vision_ingestor: Optional[VisionIngestor] = None,
        audio_ingestor: Optional[AudioIngestor] = None,
        github_ingestor: Optional[GitHubIngestor] = None,
        feed_ingestor: Optional[FeedIngestor] = None,
    ):
        self.text_ingestor = text_ingestor or TextIngestor()
        self.vision_ingestor = vision_ingestor or VisionIngestor()
        self.audio_ingestor = audio_ingestor or AudioIngestor(text_ingestor=self.text_ingestor)
        self.github_ingestor = github_ingestor or GitHubIngestor(text_ingestor=self.text_ingestor)
        self.feed_ingestor = feed_ingestor or FeedIngestor(text_ingestor=self.text_ingestor)

    async def process_text(self, user_id: str, text: str) -> list[dict]:
        """Extract concepts from plain text or chat messages."""
        return await self.text_ingestor.extract_concepts(text)

    async def process_image(self, user_id: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
        """Extract concepts, diagram descriptions, and suggested learnings from an image."""
        return await self.vision_ingestor.analyze_image(image_bytes, mime_type=mime_type)

    async def process_audio(self, user_id: str, audio_bytes: bytes) -> dict:
        """Transcribe voice note and extract concepts."""
        return await self.audio_ingestor.transcribe_and_extract(audio_bytes)

    async def process_url(self, user_id: str, url: str) -> dict:
        """Route URL to GitHub or Web/RSS scraper."""
        if "github.com" in url.lower():
            return await self.github_ingestor.ingest_repo(url)
        return await self.feed_ingestor.fetch_and_extract(url)

    async def dispatch(self, user_id: str, source_type: str, payload: dict) -> dict:
        """General dispatcher for background tasks and external ingestion webhooks."""
        if source_type == "text":
            concepts = await self.process_text(user_id, payload.get("text", ""))
            return {"source_type": source_type, "concepts": concepts}
        elif source_type == "url":
            return await self.process_url(user_id, payload.get("url", ""))
        elif source_type == "image":
            # Expect base64 or bytes
            return await self.process_image(user_id, payload.get("bytes", b""))
        elif source_type == "audio":
            return await self.process_audio(user_id, payload.get("bytes", b""))
        else:
            return {"error": f"Unsupported source type: {source_type}", "concepts": []}
