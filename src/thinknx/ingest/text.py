import json
import re
from typing import List, Dict, Any, Optional
import structlog
from thinknx.config import settings

logger = structlog.get_logger(__name__)

EXTRACT_PROMPT = """You are a concept extraction engine. Given the following text,
extract the key technical/academic concepts mentioned.

Return a JSON array of objects:
[{"name": "concept-name-kebab-case", "displayName": "Concept Name", "domain": "category", "complexity": 0.5}]

Rules:
- name: lowercase, hyphen-separated, unique identifier
- domain: one of "ai-ml", "web-dev", "databases", "devops", "math", "programming", "systems", "security", "other"
- complexity: 0.0 (beginner) to 1.0 (PhD/expert)
- Extract 2-8 concrete technical concepts
- Return ONLY valid JSON, no markdown fences or introductory text.

Text:
{text}
"""


class TextIngestor:
    """Extracts structured technical concepts from unstructured text."""

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

    async def extract_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Extract structured concept objects from text input."""
        if not text or len(text.strip()) < 5:
            return []

        if self.client:
            try:
                resp = await self.client.messages.create(
                    model=settings.model_extract,
                    max_tokens=800,
                    messages=[{"role": "user", "content": EXTRACT_PROMPT.format(text=text)}],
                )
                raw_text = resp.content[0].text.strip()
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(raw_text)
                if isinstance(data, list):
                    return data
            except Exception as e:
                logger.warning("Anthropic concept extraction error, using rule-based fallback", error=str(e))

        # Rule-based fallback extraction
        found_concepts = []
        known_keywords = {
            "transformer": ("transformers", "Transformers", "ai-ml", 0.7),
            "attention": ("attention-mechanism", "Attention Mechanism", "ai-ml", 0.7),
            "docker": ("docker", "Docker & Containers", "devops", 0.4),
            "python": ("python", "Python", "programming", 0.3),
            "neo4j": ("knowledge-graphs", "Knowledge Graphs", "databases", 0.6),
            "graph": ("knowledge-graphs", "Knowledge Graphs", "databases", 0.6),
            "rag": ("rag", "Retrieval-Augmented Generation", "ai-ml", 0.7),
            "llm": ("large-language-models", "Large Language Models", "ai-ml", 0.8),
            "fastapi": ("rest-apis", "REST APIs", "web-dev", 0.4),
            "calculus": ("calculus", "Calculus", "math", 0.4),
            "neural": ("neural-networks", "Neural Networks", "ai-ml", 0.6),
        }

        lowered = text.lower()
        for kw, (name, display, domain, complexity) in known_keywords.items():
            if kw in lowered:
                found_concepts.append({
                    "name": name,
                    "displayName": display,
                    "domain": domain,
                    "complexity": complexity
                })

        if not found_concepts:
            # Generate a generic concept from words
            words = [w for w in re.findall(r"\b[A-Za-z]{4,}\b", text) if w.lower() not in {"this", "that", "with", "from"}]
            if words:
                top_word = words[0].lower()
                found_concepts.append({
                    "name": top_word,
                    "displayName": top_word.capitalize(),
                    "domain": "programming",
                    "complexity": 0.5
                })

        return found_concepts
