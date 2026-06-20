"""Internal cache manager for reddit_scraper.

This is a support component used by the service for URL-keyed caching.
It is not part of the public facade.
"""

from __future__ import annotations

from pathlib import Path

from py_lib_runtime import BaseCacheManager, get_logger

from reddit_scraper._api.types import RedditCacheEntry
from reddit_scraper._internal.config import get_reddit_scraper_config

logger = get_logger(__name__)


def _ensure_diskcache_available() -> None:
    """Raise a clear error if the cache backend dependency is missing."""
    try:
        import diskcache
    except ModuleNotFoundError as exc:
        msg = "Install reddit-scraper with diskcache support to enable caching."
        raise ModuleNotFoundError(msg) from exc
    _ = diskcache.Cache


class RedditCacheManager(BaseCacheManager[RedditCacheEntry]):
    """URL-keyed cache manager for Reddit API responses."""

    def __init__(
        self,
        cache_dir: Path,
        *,
        max_size: int | None = None,
        compression_threshold: int | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        """Initialize the cache manager."""
        _ensure_diskcache_available()
        if max_size is None:
            config = get_reddit_scraper_config()
            max_size = int(config.cache.max_size_mb * 1024**2)
        super().__init__(
            cache_dir=cache_dir,
            max_size=max_size,
            compression_threshold=compression_threshold,
            ttl_seconds=ttl_seconds,
        )

    def _serialize_entry(self, entry: RedditCacheEntry) -> dict:
        """Serialize a cache entry for persistence."""
        return {
            "url": entry.url,
            "response_data": entry.response_data,
            "timestamp": entry.timestamp,
            "metadata": entry.metadata,
        }

    def _deserialize_entry(self, data: dict, url: str) -> RedditCacheEntry:
        """Deserialize a persisted cache entry."""
        return RedditCacheEntry(
            url=data.get("url", url),
            response_data=data.get("response_data", {}),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
        )
