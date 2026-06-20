"""Cache helpers for reddit_scraper."""

from __future__ import annotations

from typing import Any

from py_lib_runtime import get_logger

from reddit_scraper._api.types import RedditCacheEntry

logger = get_logger(__name__)


def reddit_entry_to_response(entry: RedditCacheEntry) -> dict[str, Any]:
    """Convert a cache entry into a response payload."""
    return entry.response_data


def reddit_result_to_entry(
    result: dict[str, Any], bound: dict[str, Any]
) -> RedditCacheEntry:
    """Convert a response payload into a cache entry."""
    params = bound.get("params") or {}
    return RedditCacheEntry(
        url=bound["url"],
        response_data=result,
        metadata={"params": params} if params else {},
    )


def log_reddit_cache_hit(bound: dict[str, Any]) -> None:
    """Log a cache hit for a Reddit request."""
    logger.info(
        "Cache hit",
        event_type="reddit.cache.lookup.hit",
        url=bound["url"],
    )


def log_reddit_cache_store(bound: dict[str, Any]) -> None:
    """Log a cache store for a Reddit request."""
    logger.debug(
        "Cached response",
        event_type="reddit.cache.store.succeeded",
        url=bound["url"],
    )
