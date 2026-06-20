"""Setup helpers for reddit_scraper runtime configuration."""

from __future__ import annotations

from pathlib import Path

from py_lib_runtime import resolve_cache_dir

from reddit_scraper._api.types import MediaConfig
from reddit_scraper._internal.components.cache_manager import RedditCacheManager
from reddit_scraper._internal.config import RedditScraperConfig
from reddit_scraper._internal.media_downloader.service import MediaDownloader


def resolve_network_config(
    *,
    timeout: float | None,
    random_user_agent: bool | None,
    max_retries: int | None,
    defaults: RedditScraperConfig,
) -> tuple[float, bool, int]:
    """Resolve network defaults for timeout, user agent, and retries."""
    resolved_timeout = (
        timeout if timeout is not None else defaults.network.timeout_seconds
    )
    resolved_user_agent = (
        random_user_agent
        if random_user_agent is not None
        else defaults.network.random_user_agent
    )
    resolved_retries = (
        max_retries if max_retries is not None else defaults.network.max_retries
    )
    return resolved_timeout, resolved_user_agent, resolved_retries


def resolve_cache_config(
    *,
    cache_enabled: bool | None,
    cache_dir: str | None,
    cache_max_size_mb: float | None,
    defaults: RedditScraperConfig,
) -> tuple[bool, str | None, float]:
    """Resolve cache defaults and overrides."""
    resolved_enabled = (
        cache_enabled if cache_enabled is not None else defaults.cache.enabled
    )
    resolved_dir = cache_dir or defaults.cache.cache_dir
    resolved_max_size = (
        cache_max_size_mb
        if cache_max_size_mb is not None
        else defaults.cache.max_size_mb
    )
    if resolved_enabled:
        resolved_path = resolve_cache_dir(
            resolved_dir,
            namespace="reddit_scraper",
        )
        resolved_dir = str(resolved_path) if resolved_path is not None else None
    else:
        resolved_dir = None
    return resolved_enabled, resolved_dir, resolved_max_size


def resolve_media_config(
    *,
    media_config: MediaConfig | None,
    media_cache_dir: str | None,
    defaults: RedditScraperConfig,
) -> tuple[MediaConfig | None, str | None]:
    """Resolve media downloader defaults."""
    resolved_media_config = media_config
    resolved_media_cache_dir = media_cache_dir
    if resolved_media_config is None and defaults.media.enabled:
        resolved_media_config = defaults.media.to_media_config()
        resolved_media_cache_dir = resolved_media_cache_dir or defaults.media.cache_dir
    if resolved_media_cache_dir is None and resolved_media_config is not None:
        resolved_media_path = resolve_cache_dir(None, namespace="reddit_scraper/media")
        if resolved_media_path is not None:
            resolved_media_cache_dir = str(resolved_media_path)
    return resolved_media_config, resolved_media_cache_dir


def init_cache(
    *,
    enabled: bool,
    cache_dir: str | None,
    cache_max_size_mb: float,
) -> RedditCacheManager | None:
    """Initialize cache manager if enabled."""
    if not enabled:
        return None
    cache_path = Path(cache_dir).expanduser() if cache_dir else None
    if cache_path is None:
        return None
    return RedditCacheManager(
        cache_dir=cache_path,
        max_size=int(cache_max_size_mb * 1024**2),
    )


def init_media_downloader(
    *,
    media_config: MediaConfig | None,
    media_cache_dir: str | None,
    proxy: str | None,
    http_client: object,
) -> MediaDownloader | None:
    """Initialize media downloader when configured."""
    if media_config is None:
        return None
    return MediaDownloader(
        config=media_config,
        cache_dir=Path(media_cache_dir).expanduser() if media_cache_dir else None,
        http_client=http_client,
        proxy=proxy,
    )
