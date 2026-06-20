"""Reddit scraping service implementation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cache
from typing import Any, cast

import httpx
from py_lib_runtime import (
    CacheConfig,
    CacheEvents,
    cache_from_self_attr,
    cached,
    get_logger,
    log_operation_duration,
)
from tenacity import RetryCallState

from reddit_scraper._api.types import (
    ClientOptions,
    MediaConfig,
    MediaItem,
    SearchOptions,
    SubredditSearchOptions,
)
from reddit_scraper._internal.components.cache import (
    log_reddit_cache_hit,
    log_reddit_cache_store,
    reddit_entry_to_response,
    reddit_result_to_entry,
)
from reddit_scraper._internal.components.feeds import FeedMixin
from reddit_scraper._internal.components.fetch import get_json_response
from reddit_scraper._internal.components.http import (
    build_headers,
    create_http_client,
    create_user_agent,
)
from reddit_scraper._internal.components.post_details import parse_post_details
from reddit_scraper._internal.components.request import RequestSpec, perform_get
from reddit_scraper._internal.components.resolver import (
    ResolvedClientConfig,
    get_default_reddit_scraper_resolver,
)
from reddit_scraper._internal.components.search import build_type_param
from reddit_scraper._internal.components.search_parsing import handle_search_results
from reddit_scraper._internal.components.setup import (
    init_cache,
    init_media_downloader,
    resolve_cache_config,
    resolve_media_config,
    resolve_network_config,
)
from reddit_scraper._internal.components.users import UserMixin
from reddit_scraper._internal.config import get_reddit_scraper_config

logger = get_logger(__name__)


@dataclass(frozen=True)
class ScraperConfig:
    """Configuration for RedditScraper initialization."""

    # pylint: disable=too-many-instance-attributes

    proxy: str | None = None
    timeout: float | None = None
    random_user_agent: bool | None = None
    max_retries: int | None = None
    cache_dir: str | None = None
    cache_enabled: bool | None = None
    cache_max_size_mb: float | None = None
    media_config: MediaConfig | None = None
    media_cache_dir: str | None = None


class RedditScraper(UserMixin, FeedMixin):
    """Fetch Reddit data with caching, retries, and optional media downloads."""

    # pylint: disable=too-many-instance-attributes

    __slots__ = (
        "_cache",
        "_max_retries",
        "_media_downloader",
        "_ua",
        "client",
        "proxy",
        "timeout",
    )

    def __init__(self, config: ScraperConfig | None = None) -> None:
        """Initialize the Reddit scraper.

        Args:
            config: Optional configuration object
        """
        if config is None:
            config = ScraperConfig()

        defaults = get_reddit_scraper_config()
        self.proxy = config.proxy
        (
            self.timeout,
            random_user_agent,
            self._max_retries,
        ) = resolve_network_config(
            timeout=config.timeout,
            random_user_agent=config.random_user_agent,
            max_retries=config.max_retries,
            defaults=defaults,
        )
        self._ua = create_user_agent(enabled=random_user_agent)

        cache_enabled, cache_dir, cache_max_size_mb = resolve_cache_config(
            cache_enabled=config.cache_enabled,
            cache_dir=config.cache_dir,
            cache_max_size_mb=config.cache_max_size_mb,
            defaults=defaults,
        )
        self._cache = init_cache(
            enabled=cache_enabled,
            cache_dir=cache_dir,
            cache_max_size_mb=cache_max_size_mb,
        )

        self.client = create_http_client(
            timeout=self.timeout,
            max_retries=self._max_retries,
            proxy=config.proxy,
        )

        media_config, media_cache_dir = resolve_media_config(
            media_config=config.media_config,
            media_cache_dir=config.media_cache_dir,
            defaults=defaults,
        )
        self._media_downloader = init_media_downloader(
            media_config=media_config,
            media_cache_dir=media_cache_dir,
            proxy=config.proxy,
            http_client=self.client,
        )

    def __enter__(self) -> RedditScraper:
        """Enter the context manager and return the scraper."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Exit the context manager and close resources."""
        self.close()

    def _get_headers(self) -> dict[str, str]:
        """Get headers with random user agent if enabled."""
        return build_headers(self._ua)

    def _get(
        self,
        url: str,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        """Execute a raw GET request through the scraper client."""
        return perform_get(
            RequestSpec(
                client=self.client,
                url=url,
                params=params,
                headers=self._get_headers(),
                max_retries=self._max_retries,
                before_sleep=self._before_sleep_callback,
            )
        )

    def _before_sleep_callback(self, retry_state: RetryCallState) -> None:
        """Log a warning before retrying a failed attempt."""
        next_action = retry_state.next_action
        outcome = retry_state.outcome
        sleep_time = next_action.sleep if next_action else 0.0
        exc = outcome.exception() if outcome else None
        logger.warning(
            "Retrying request",
            event_type="reddit.request.retry.started",
            sleep_time=sleep_time,
            attempt_number=retry_state.attempt_number,
            error={
                "message": str(exc) if exc else "Unknown error",
                "type": type(exc).__name__ if exc else "UnknownError",
            },
        )

    @cached(
        cache_from_self_attr("_cache"),
        options=CacheConfig(
            key_arg="url",
            params_arg="params",
            to_entry=reddit_result_to_entry,
            from_entry=reddit_entry_to_response,
        ),
        events=CacheEvents(
            on_hit=log_reddit_cache_hit,
            on_store=log_reddit_cache_store,
        ),
    )
    def _get_cached_or_fetch(
        self, url: str, params: dict[str, Any] | None = None
    ) -> object | None:
        """Get response from cache or fetch from network."""
        return get_json_response(
            lambda: perform_get(
                RequestSpec(
                    client=self.client,
                    url=url,
                    params=params,
                    headers=self._get_headers(),
                    max_retries=self._max_retries,
                    before_sleep=self._before_sleep_callback,
                )
            ),
            url=url,
        )

    def _fetch_json_page(
        self,
        url: str,
        params: dict[str, Any],
        *,
        cache_first_page: bool,
        context: str,
    ) -> dict[str, Any] | None:
        """Fetch a JSON response for a listing page."""
        if cache_first_page:
            return self._get_cached_or_fetch(url, params)
        return get_json_response(
            lambda: perform_get(
                RequestSpec(
                    client=self.client,
                    url=url,
                    params=params,
                    headers=self._get_headers(),
                    max_retries=self._max_retries,
                    before_sleep=self._before_sleep_callback,
                )
            ),
            url=url,
            context=context,
        )

    def scrape_post_details(
        self, permalink: str, *, correlation_id: str | None = None
    ) -> dict[str, Any] | None:
        """Fetch a post along with its comments."""
        with log_operation_duration(
            logger,
            event_type="reddit.post.details.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
            permalink=permalink,
        ):
            url = f"https://www.reddit.com{permalink}.json"
            data = cast("list[dict[str, Any]] | None", self._get_cached_or_fetch(url))
            return parse_post_details(
                data,
                permalink=permalink,
                url=url,
                extract_comments=self._extract_comments,
            )

    def search_reddit(
        self,
        query: str,
        *,
        options: SearchOptions | None = None,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search Reddit globally.

        Args:
            query: Search query string
            options: Optional search options (limit, cursors, types)
            correlation_id: Optional ID for correlating related operations.

        Returns:
            List of search result dicts
        """
        with log_operation_duration(
            logger,
            event_type="reddit.search.global.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
            query=query,
        ):
            resolver = get_default_reddit_scraper_resolver()
            options = resolver.resolve_search_options(options)
            limit = options.limit
            search_types = options.search_types

            url = "https://www.reddit.com/search.json"
            params = {
                "q": query,
                "limit": limit,
                "sort": "relevance",
                "type": build_type_param(search_types),
            }
            if options.after:
                params["after"] = options.after
            if options.before:
                params["before"] = options.before
            data = cast(
                "dict[str, Any] | None",
                self._get_cached_or_fetch(url, params),
            )
            if data is None:
                return []
            return handle_search_results(data, query=query)

    def search_subreddit(
        self,
        subreddit: str,
        query: str,
        *,
        options: SubredditSearchOptions | None = None,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search within a specific subreddit.

        Args:
            subreddit: Subreddit name (without r/)
            query: Search query string
            options: Optional search options (limit, cursors, sort, types)
            correlation_id: Optional ID for correlating related operations.

        Returns:
            List of search result dicts
        """
        with log_operation_duration(
            logger,
            event_type="reddit.search.subreddit.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
            subreddit=subreddit,
            query=query,
        ):
            resolver = get_default_reddit_scraper_resolver()
            options = resolver.resolve_subreddit_search_options(options)
            limit = options.limit
            sort = options.sort
            search_types = options.search_types

            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {
                "q": query,
                "limit": limit,
                "sort": sort,
                "type": build_type_param(search_types),
                "restrict_sr": "on",
            }
            if options.after:
                params["after"] = options.after
            if options.before:
                params["before"] = options.before
            data = cast(
                "dict[str, Any] | None",
                self._get_cached_or_fetch(url, params),
            )
            if data is None:
                return []
            return handle_search_results(data, query=query)

    def cache_stats(self, *, correlation_id: str | None = None) -> dict:
        """Get cache statistics."""
        with log_operation_duration(
            logger,
            event_type="reddit.cache.stats.completed",
            level=logging.DEBUG,
            correlation_id=correlation_id,
        ):
            if self._cache is None:
                return {
                    "enabled": False,
                    "directory": "",
                    "size_bytes": 0,
                    "entry_count": 0,
                    "max_size_bytes": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "ttl_enabled": False,
                    "ttl_seconds": None,
                    "compression_enabled": False,
                    "compression_threshold_bytes": None,
                    "compressed_entries": 0,
                    "compressed_bytes_in": 0,
                    "compressed_bytes_out": 0,
                    "compression_savings_bytes": 0,
                }
            return self._cache.stats()

    def clear_cache(self, *, correlation_id: str | None = None) -> None:
        """Clear all cached entries."""
        with log_operation_duration(
            logger,
            event_type="reddit.cache.clear.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
        ):
            if self._cache is not None:
                self._cache.clear()

    def download_media(
        self,
        post_data: dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> list[MediaItem]:
        """Download media from a post.

        Args:
            post_data: Raw post data from Reddit API
            correlation_id: Optional ID for correlating related operations.

        Returns:
            List of downloaded MediaItems (empty if media disabled)
        """
        with log_operation_duration(
            logger,
            event_type="reddit.media.download.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
        ):
            if self._media_downloader is None:
                return []
            return self._media_downloader.download_from_post(post_data)

    def media_stats(self, *, correlation_id: str | None = None) -> dict[str, Any]:
        """Get media download statistics."""
        with log_operation_duration(
            logger,
            event_type="reddit.media.stats.completed",
            level=logging.DEBUG,
            correlation_id=correlation_id,
        ):
            if self._media_downloader is None:
                return {"enabled": False}
            return self._media_downloader.stats()

    def close(self, *, correlation_id: str | None = None) -> None:
        """Close the HTTP client, cache, and media downloader."""
        with log_operation_duration(
            logger,
            event_type="reddit.client.close.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
        ):
            if self._media_downloader:
                self._media_downloader.close()
            self.client.close()
            if self._cache is not None:
                self._cache.close()


def _build_scraper_config(resolved: ResolvedClientConfig) -> ScraperConfig:
    """Build ScraperConfig from resolved client settings."""
    return ScraperConfig(
        proxy=resolved.proxy,
        timeout=resolved.timeout,
        random_user_agent=resolved.random_user_agent,
        max_retries=resolved.max_retries,
        cache_dir=resolved.cache_dir,
        cache_enabled=resolved.cache_enabled,
        cache_max_size_mb=resolved.cache_max_size_mb,
        media_config=resolved.media_config,
        media_cache_dir=resolved.media_cache_dir,
    )


def create_reddit_scraper_service(
    *,
    client: ClientOptions | None = None,
    media_config: MediaConfig | None = None,
    media_cache_dir: str | None = None,
) -> RedditScraper:
    """Create a configured RedditScraper instance."""
    resolver = get_default_reddit_scraper_resolver()
    resolved = resolver.resolve_client_config(
        client,
        media_config=media_config,
        media_cache_dir=media_cache_dir,
    )
    return RedditScraper(config=_build_scraper_config(resolved))


@cache
def get_default_reddit_scraper_service() -> RedditScraper:
    """Return a cached, default-configured service instance."""
    return create_reddit_scraper_service()


def get_reddit_scraper_service(
    *,
    client: ClientOptions | None = None,
    media_config: MediaConfig | None = None,
    media_cache_dir: str | None = None,
) -> RedditScraper:
    """Get a default scraper or create one with custom options."""
    if client is None and media_config is None and media_cache_dir is None:
        return get_default_reddit_scraper_service()
    return create_reddit_scraper_service(
        client=client,
        media_config=media_config,
        media_cache_dir=media_cache_dir,
    )


def close_default_reddit_scraper_service() -> None:
    """Close and clear the cached default scraper instance."""
    if get_default_reddit_scraper_service.cache_info().currsize == 0:
        get_default_reddit_scraper_service.cache_clear()
        return
    try:
        scraper = get_default_reddit_scraper_service()
    # Defensive: if cached service construction failed, ensure we still clear the cache.
    except Exception:
        get_default_reddit_scraper_service.cache_clear()
        return
    scraper.close()
    get_default_reddit_scraper_service.cache_clear()
