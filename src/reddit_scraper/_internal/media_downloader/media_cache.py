"""Cache integration helpers for the media_downloader domain."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from py_lib_runtime import get_logger

from reddit_scraper._api.errors import CacheError
from reddit_scraper._api.types import MediaItem
from reddit_scraper._internal.media_downloader.cache_manager import MediaCacheManager
from reddit_scraper._internal.media_downloader.types import MediaCacheEntry

logger = get_logger(__name__)


def init_media_cache(
    *,
    enabled: bool,
    cache_media: bool,
    cache_dir: Path | None,
    max_size_bytes: int,
) -> MediaCacheManager | None:
    """Create a media cache manager when caching is enabled."""
    if not (enabled and cache_media and cache_dir is not None):
        return None
    return MediaCacheManager(
        cache_dir=cache_dir,
        max_size=max_size_bytes,
        compression_threshold=None,
    )


def get_cached_media(cache: MediaCacheManager | None, url: str) -> MediaItem | None:
    """Read a cached media entry as a `MediaItem` if present."""
    if cache is None:
        return None

    try:
        entry = cache.get(url)
    except Exception as exc:  # Defensive: cache backend can fail.
        error = CacheError(operation="read", url=url, cause=exc)
        logger.warning(
            "Cache read failed",
            event_type="reddit_scraper.media.cache.read_error",
            url=url,
            error={"message": str(error), "type": type(error).__name__},
            exc_info=exc,
        )
        return None

    if entry is None:
        return None

    return MediaItem(
        url=url,
        content=entry.content,
        content_type=entry.content_type,
        extension=entry.extension,
        size_bytes=entry.size_bytes,
        from_cache=True,
        timestamp=entry.timestamp,
    )


def save_media_to_cache(cache: MediaCacheManager | None, item: MediaItem) -> None:
    """Persist a downloaded media item into the cache (best-effort)."""
    if cache is None:
        return

    entry = MediaCacheEntry(
        url=item.url,
        content=item.content,
        content_type=item.content_type,
        extension=item.extension,
        size_bytes=item.size_bytes,
        timestamp=datetime.now(UTC).isoformat(),
    )
    try:
        cache.set(item.url, entry)
    except Exception as exc:  # Defensive: cache backend can fail.
        error = CacheError(operation="write", url=item.url, cause=exc)
        logger.warning(
            "Cache write failed",
            event_type="reddit_scraper.media.cache.write_error",
            url=item.url,
            error={"message": str(error), "type": type(error).__name__},
            exc_info=exc,
        )
