"""Runtime config snapshot state.

Why:
    Keeps process-wide config construction and install/read helpers inside the
    private config implementation.
"""

from __future__ import annotations

from threading import RLock

from py_lib_runtime import get_logger

from reddit_scraper._internal.config.assembly import build_default_config
from reddit_scraper._internal.config.models import RedditScraperConfig
from reddit_scraper._internal.config.validation import validate_config

_installed_config: RedditScraperConfig = build_default_config()
_config_lock = RLock()
logger = get_logger(__name__)


def get_reddit_scraper_config(
    config: RedditScraperConfig | None = None,
) -> RedditScraperConfig:
    """Return a validated runtime configuration snapshot."""
    if config is not None:
        return config
    with _config_lock:
        return _installed_config


def install_reddit_scraper_config(config: object) -> RedditScraperConfig:
    """Install a validated runtime configuration snapshot."""
    if not isinstance(config, RedditScraperConfig):
        msg = "install_reddit_scraper_config() expects a RedditScraperConfig instance."
        raise TypeError(msg)

    validate_config(config)
    global _installed_config  # noqa: PLW0603
    with _config_lock:
        _installed_config = config

    _clear_runtime_config_caches()
    logger.info(
        "Configuration installed",
        event_type="reddit_scraper.config.runtime.installed",
        network_timeout_seconds=config.network.timeout_seconds,
        network_max_retries=config.network.max_retries,
        cache_enabled=config.cache.enabled,
        media_enabled=config.media.enabled,
    )
    return config


def _clear_runtime_config_caches() -> None:
    """Clear runtime singletons that captured the previous config snapshot."""
    from reddit_scraper._internal.components.resolver import (
        get_default_reddit_scraper_resolver,
    )
    from reddit_scraper._internal.scraper.service import (
        close_default_reddit_scraper_service,
    )

    close_default_reddit_scraper_service()
    get_default_reddit_scraper_resolver.cache_clear()
