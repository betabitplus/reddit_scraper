"""Resolves public inputs into validated, defaulted reddit_scraper DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING

from py_lib_runtime import resolve_cache_dir

from reddit_scraper._api.types import (
    ClientOptions,
    FeedOptions,
    PopularFeedOptions,
    SearchOptions,
    SubredditPostsOptions,
    SubredditSearchOptions,
)
from reddit_scraper._internal.config import (
    RedditScraperConfig,
    get_reddit_scraper_config,
)

if TYPE_CHECKING:
    from reddit_scraper._api.types import MediaConfig


@dataclass(frozen=True)
# pylint: disable=too-many-instance-attributes
class ResolvedClientConfig:
    """Resolved, defaulted client configuration."""

    proxy: str | None
    timeout: float
    random_user_agent: bool
    max_retries: int
    cache_dir: str | None
    cache_enabled: bool
    cache_max_size_mb: float
    media_config: MediaConfig | None
    media_cache_dir: str | None


class RedditScraperResolver:
    """Resolves untrusted input into validated, defaulted DTOs."""

    def __init__(self) -> None:
        """Initialize resolver with cached config."""
        self._config = get_reddit_scraper_config()

    def _resolve_cache_dir(
        self,
        *,
        cache_enabled: bool,
        cache_dir: str | None,
    ) -> str | None:
        """Resolve cache directory when caching is enabled."""
        if not cache_enabled:
            return None
        resolved_path = resolve_cache_dir(
            cache_dir,
            namespace="reddit_scraper",
        )
        return str(resolved_path) if resolved_path is not None else None

    def _resolve_media_config(
        self,
        *,
        defaults: RedditScraperConfig,
        media_config: MediaConfig | None,
        media_cache_dir: str | None,
    ) -> tuple[MediaConfig | None, str | None]:
        """Resolve media downloader defaults and cache directory."""
        resolved_media_config = media_config
        resolved_media_cache_dir = media_cache_dir
        if resolved_media_config is None and defaults.media.enabled:
            resolved_media_config = defaults.media.to_media_config()
            resolved_media_cache_dir = (
                resolved_media_cache_dir or defaults.media.cache_dir
            )
        if resolved_media_cache_dir is None and resolved_media_config is not None:
            resolved_media_path = resolve_cache_dir(
                None,
                namespace="reddit_scraper/media",
            )
            if resolved_media_path is not None:
                resolved_media_cache_dir = str(resolved_media_path)
        return resolved_media_config, resolved_media_cache_dir

    def resolve_client_config(
        self,
        client: ClientOptions | None,
        *,
        media_config: MediaConfig | None = None,
        media_cache_dir: str | None = None,
    ) -> ResolvedClientConfig:
        """Resolve client options and media defaults."""
        if client is None:
            client = ClientOptions()

        defaults = self._config
        resolved_timeout = (
            defaults.network.timeout_seconds
            if client.timeout is None
            else client.timeout
        )
        resolved_cache_enabled = (
            defaults.cache.enabled
            if client.cache_enabled is None
            else client.cache_enabled
        )
        resolved_cache_dir = self._resolve_cache_dir(
            cache_enabled=resolved_cache_enabled,
            cache_dir=client.cache_dir or defaults.cache.cache_dir,
        )
        resolved_media_config, resolved_media_cache_dir = self._resolve_media_config(
            defaults=defaults,
            media_config=media_config,
            media_cache_dir=media_cache_dir,
        )

        return ResolvedClientConfig(
            proxy=client.proxy,
            timeout=resolved_timeout,
            random_user_agent=defaults.network.random_user_agent,
            max_retries=defaults.network.max_retries,
            cache_dir=resolved_cache_dir,
            cache_enabled=resolved_cache_enabled,
            cache_max_size_mb=defaults.cache.max_size_mb,
            media_config=resolved_media_config,
            media_cache_dir=resolved_media_cache_dir,
        )

    def resolve_search_options(self, options: SearchOptions | None) -> SearchOptions:
        """Apply config defaults to global search options."""
        defaults = self._config.defaults.search
        if options is None:
            options = SearchOptions()
        return SearchOptions(
            limit=defaults.limit if options.limit is None else options.limit,
            after=options.after,
            before=options.before,
            search_types=(
                list(defaults.search_types)
                if options.search_types is None
                else options.search_types
            ),
        )

    def resolve_subreddit_search_options(
        self,
        options: SubredditSearchOptions | None,
    ) -> SubredditSearchOptions:
        """Apply config defaults to subreddit search options."""
        defaults = self._config.defaults.subreddit_search
        if options is None:
            options = SubredditSearchOptions()
        return SubredditSearchOptions(
            limit=defaults.limit if options.limit is None else options.limit,
            after=options.after,
            before=options.before,
            search_types=(
                list(defaults.search_types)
                if options.search_types is None
                else options.search_types
            ),
            sort=defaults.sort if options.sort is None else options.sort,
        )

    def resolve_feed_options(self, options: FeedOptions | None) -> FeedOptions:
        """Apply config defaults to global feed options."""
        defaults = self._config.defaults.feed
        if options is None:
            options = FeedOptions()
        return FeedOptions(
            limit=defaults.limit if options.limit is None else options.limit,
            category=(
                defaults.category if options.category is None else options.category
            ),
            time_filter=(
                defaults.time_filter
                if options.time_filter is None
                else options.time_filter
            ),
        )

    def resolve_popular_feed_options(
        self,
        options: PopularFeedOptions | None,
    ) -> PopularFeedOptions:
        """Apply config defaults to popular feed options."""
        defaults = self._config.defaults.popular_feed
        if options is None:
            options = PopularFeedOptions()
        return PopularFeedOptions(
            limit=defaults.limit if options.limit is None else options.limit,
            category=(
                defaults.category if options.category is None else options.category
            ),
            time_filter=(
                defaults.time_filter
                if options.time_filter is None
                else options.time_filter
            ),
            geo_filter=(
                defaults.geo_filter
                if options.geo_filter is None
                else options.geo_filter
            ),
        )

    def resolve_subreddit_posts_options(
        self,
        options: SubredditPostsOptions | None,
    ) -> SubredditPostsOptions:
        """Apply config defaults to subreddit post options."""
        defaults = self._config.defaults.subreddit_posts
        if options is None:
            options = SubredditPostsOptions()
        return SubredditPostsOptions(
            limit=defaults.limit if options.limit is None else options.limit,
            category=(
                defaults.category if options.category is None else options.category
            ),
            time_filter=(
                defaults.time_filter
                if options.time_filter is None
                else options.time_filter
            ),
        )

    def resolve_user_limit(self, limit: int | None) -> int:
        """Apply config defaults to user data limits."""
        return self._config.defaults.user_data.limit if limit is None else limit


@cache
def get_default_reddit_scraper_resolver() -> RedditScraperResolver:
    """Return a cached resolver instance."""
    return RedditScraperResolver()
