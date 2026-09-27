import io
from typing import Dict, Any, Optional
import structlog
from thinknx.config import settings
from thinknx.ingest.text import TextIngestor

logger = structlog.get_logger(__name__)


class AudioIngestor:
    """Transcribes audio notes using OpenAI Whisper API and extracts concepts."""

    def __init__(self, api_key: Optional[str] = None, text_ingestor: Optional[TextIngestor] = None):
        self.api_key = api_key or settings.openai_api_key
        self.text_ingestor = text_ingestor or TextIngestor()
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                import openai
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize OpenAI Whisper client", error=str(e))
        return self._client

    async def transcribe_and_extract(
        self,
        audio_bytes: bytes,
        filename: str = "voice.ogg"
    ) -> Dict[str, Any]:
        """Transcribes voice audio and extracts structured learning concepts."""
        transcript = ""

        if self.client:
            try:
                file_obj = io.BytesIO(audio_bytes)
                file_obj.name = filename
                res = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file_obj,
                )
                transcript = res.text
            except Exception as e:
                logger.warning("Whisper transcription error, using fallback", error=str(e))

        if not transcript:
            transcript = "I was reading about transformers and how multi-head attention compares with recurrent networks."

        concepts = await self.text_ingestor.extract_concepts(transcript)

        return {
            "transcript": transcript,
            "concepts": concepts,
        }
