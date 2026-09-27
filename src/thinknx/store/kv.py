from typing import Optional, Any
import httpx
import structlog
from thinknx.config import settings

logger = structlog.get_logger(__name__)


class KV2Store:
    """
    Hostinger KV2 Key-Value Store REST Client with automatic local in-memory fallback.
    Supports GET, SET, and DELETE operations with optional TTL expiration.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 5.0
    ):
        self.endpoint = (endpoint or settings.kv2_endpoint).rstrip("/")
        self.token = token or settings.kv2_token
        self.timeout = timeout
        self._memory_cache: dict[str, Any] = {}

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.token)

    async def get(self, key: str) -> Optional[str]:
        """Fetch string value by key."""
        if not self.is_configured:
            return self._memory_cache.get(key)

        url = f"{self.endpoint}/api/v1/kv/{key}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("value")
                elif resp.status_code == 404:
                    return None
        except Exception as e:
            logger.warning("KV2 GET request failed, falling back to memory", key=key, error=str(e))
        return self._memory_cache.get(key)

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """Store string value by key with optional TTL."""
        self._memory_cache[key] = value

        if not self.is_configured:
            return True

        url = f"{self.endpoint}/api/v1/kv/{key}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"value": value}
        if ttl_seconds:
            payload["ttl"] = ttl_seconds

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                return resp.status_code in (200, 201)
        except Exception as e:
            logger.warning("KV2 SET request failed", key=key, error=str(e))
            return True

    async def delete(self, key: str) -> bool:
        """Delete key from KV2."""
        self._memory_cache.pop(key, None)

        if not self.is_configured:
            return True

        url = f"{self.endpoint}/api/v1/kv/{key}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.delete(url, headers=headers)
                return resp.status_code in (200, 204, 404)
        except Exception as e:
            logger.warning("KV2 DELETE request failed", key=key, error=str(e))
            return True
