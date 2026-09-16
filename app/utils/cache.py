"""Caching utility with SHA-256 content hash support."""

import hashlib
import time
from typing import Optional, Any, Dict


class MemoryCache:
    """Thread-safe TTL in-memory cache with fallback interface."""

    def __init__(self, default_ttl: int = 3600):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        if time.time() > item["expires_at"]:
            del self._store[key]
            return None
        return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = {"value": value, "expires_at": time.time() + ttl}

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


def compute_content_hash(content: str) -> str:
    """Computes a deterministic SHA-256 hash of normalized text or URL."""
    normalized = " ".join(content.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# Global cache instance
cache = MemoryCache()
