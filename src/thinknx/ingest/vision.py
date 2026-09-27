import base64
import json
from typing import Dict, Any, Optional
import structlog
from thinknx.config import settings

logger = structlog.get_logger(__name__)

VISION_PROMPT = """Look at this image and extract the key technical or academic concepts shown.
This could be an architecture diagram, whiteboard photo, mathematical proof, textbook page, code snippet, or slide.

Return valid JSON:
{
  "description": "Brief description of what the image shows",
  "concepts": [
    {"name": "concept-kebab-case", "displayName": "Concept Name", "domain": "category", "complexity": 0.5}
  ],
  "suggested_learning": "One clear sentence suggesting what the user might want to learn or explore next"
}

Return ONLY valid JSON.
"""


class VisionIngestor:
    """Analyzes diagrams, whiteboard photos, formulas, and screenshots using Claude Vision."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize Anthropic client", error=str(e))
        return self._client

    async def analyze_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """Process image bytes and extract technical concepts with learning suggestions."""
        if self.client:
            try:
                b64_data = base64.b64encode(image_bytes).decode("utf-8")
                resp = await self.client.messages.create(
                    model=settings.model_vision,
                    max_tokens=1000,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": b64_data,
                                    },
                                },
                                {"type": "text", "text": VISION_PROMPT},
                            ],
                        }
                    ],
                )
                text = resp.content[0].text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                return json.loads(text)
            except Exception as e:
                logger.warning("Claude Vision processing error, using fallback", error=str(e))

        # Fallback simulation
        return {
            "description": "Architectural diagram showing neural network components and data flow.",
            "concepts": [
                {"name": "neural-networks", "displayName": "Neural Networks", "domain": "ai-ml", "complexity": 0.6},
                {"name": "attention-mechanism", "displayName": "Attention Mechanism", "domain": "ai-ml", "complexity": 0.7},
                {"name": "transformers", "displayName": "Transformers", "domain": "ai-ml", "complexity": 0.7},
            ],
            "suggested_learning": "Dive into how self-attention layers process sequence embeddings in parallel.",
        }
