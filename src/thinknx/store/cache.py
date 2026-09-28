import hashlib
import json
from typing import Optional, Any
import structlog

from thinknx.store.kv import KV2Store

logger = structlog.get_logger(__name__)


class LLMCache:
    """
    Cache for LLM generation responses indexed by SHA256(model + prompt + json_kwargs).
    Prevents repeated expensive inference calls on identical prompts.
    """

    def __init__(self, store: Optional[KV2Store] = None, default_ttl: int = 86400 * 7):
        self.store = store or KV2Store()
        self.default_ttl = default_ttl

    def _make_key(self, model: str, prompt: str, kwargs: Optional[dict] = None) -> str:
        content = f"{model}:{prompt}:{json.dumps(kwargs or {}, sort_keys=True)}"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return f"llm_cache:{digest}"

    async def get(self, model: str, prompt: str, kwargs: Optional[dict] = None) -> Optional[str]:
        """Lookup cached response."""
        key = self._make_key(model, prompt, kwargs)
        try:
            return await self.store.get(key)
        except Exception as e:
            logger.warning("Cache lookup error", error=str(e))
            return None

    async def get_json(self, model: str, prompt: str, kwargs: Optional[dict] = None) -> Optional[Any]:
        """Lookup cached response and parse as JSON."""
        raw = await self.get(model, prompt, kwargs)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    async def set(
        self,
        model: str,
        prompt: str,
        response: str,
        kwargs: Optional[dict] = None,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Store LLM response in cache."""
        key = self._make_key(model, prompt, kwargs)
        ttl = ttl_seconds or self.default_ttl
        try:
            return await self.store.set(key, response, ttl_seconds=ttl)
        except Exception as e:
            logger.warning("Cache store error", error=str(e))
            return False

    async def set_json(
        self,
        model: str,
        prompt: str,
        data: Any,
        kwargs: Optional[dict] = None,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Serialize data as JSON and store in cache."""
        try:
            serialized = json.dumps(data, default=str)
        except (TypeError, ValueError):
            return False
        return await self.set(model, prompt, serialized, kwargs=kwargs, ttl_seconds=ttl_seconds)


response_cache = LLMCache()
