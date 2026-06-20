"""Runtime config validation helpers.

Why:
    Centralizes config invariant checks before snapshots are constructed or
    installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from reddit_scraper._api import defaults as api_defaults
from reddit_scraper._api.errors import InvalidConfigValueError

if TYPE_CHECKING:
    from reddit_scraper._internal.config.models import (
        DefaultsConfig,
        FeedDefaultsConfig,
        MediaDownloadConfig,
        NetworkConfig,
        PopularFeedDefaultsConfig,
        RateLimitConfig,
        RedditCacheConfig,
        RedditScraperConfig,
        SearchDefaultsConfig,
        SubredditPostsDefaultsConfig,
        SubredditSearchDefaultsConfig,
        UserDataDefaultsConfig,
    )


def _validate_number(
    *,
    field_name: str,
    value: object,
    minimum: float,
    maximum: float | None = None,
    include_minimum: bool = True,
) -> None:
    """Validate numeric config bounds before defaults become executable."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidConfigValueError(
            field=field_name,
            value=value,
            reason="must be a number",
        )
    if include_minimum:
        is_too_small = value < minimum
        minimum_reason = f"must be greater than or equal to {minimum:g}"
    else:
        is_too_small = value <= minimum
        minimum_reason = f"must be greater than {minimum:g}"
    if is_too_small:
        raise InvalidConfigValueError(
            field=field_name,
            value=value,
            reason=minimum_reason,
        )
    if maximum is not None and value > maximum:
        raise InvalidConfigValueError(
            field=field_name,
            value=value,
            reason=f"must be less than or equal to {maximum:g}",
        )


def _coerce_tuple(
    *,
    field_name: str,
    value: object,
    supported: tuple[str, ...],
    value_label: str,
) -> tuple[str, ...]:
    """Normalize list/set/tuple config catalogs into immutable tuples."""
    if isinstance(value, set):
        value = tuple(sorted(value))
    elif isinstance(value, list):
        value = tuple(value)
    if not isinstance(value, tuple):
        raise InvalidConfigValueError(
            field=field_name,
            value=value,
            reason=f"must be a list, set, or tuple of {value_label}",
        )
    invalid = [item for item in value if item not in supported]
    if invalid:
        raise InvalidConfigValueError(
            field=field_name,
            value=invalid,
            reason=f"must be one of {list(supported)}",
        )
    return value


def _validate_member(
    *,
    field_name: str,
    value: object,
    supported: tuple[str, ...],
) -> str:
    """Validate one string config value against a stable catalog."""
    if not isinstance(value, str) or value not in supported:
        raise InvalidConfigValueError(
            field=field_name,
            value=value,
            reason=f"must be one of {list(supported)}",
        )
    return value


def validate_network_config(config: NetworkConfig) -> None:
    """Validate network defaults."""
    _validate_number(
        field_name="network.timeout_seconds",
        value=config.timeout_seconds,
        minimum=0.1,
    )
    _validate_number(
        field_name="network.max_retries",
        value=config.max_retries,
        minimum=0,
    )


def validate_cache_config(config: RedditCacheConfig) -> None:
    """Validate cache defaults."""
    _validate_number(
        field_name="cache.max_size_mb",
        value=config.max_size_mb,
        minimum=0,
    )


def validate_media_download_config(config: MediaDownloadConfig) -> tuple[str, ...]:
    """Validate media defaults and return normalized allowed types."""
    allowed_types = _coerce_tuple(
        field_name="media.allowed_types",
        value=config.allowed_types,
        supported=api_defaults.SUPPORTED_MEDIA_DOWNLOAD_TYPES,
        value_label="media type strings",
    )
    _validate_number(
        field_name="media.max_file_size_mb",
        value=config.max_file_size_mb,
        minimum=0,
    )
    _validate_number(
        field_name="media.max_downloads_per_post",
        value=config.max_downloads_per_post,
        minimum=0,
    )
    _validate_number(
        field_name="media.max_total_downloads",
        value=config.max_total_downloads,
        minimum=0,
    )
    _validate_number(
        field_name="media.proxy_size_threshold_mb",
        value=config.proxy_size_threshold_mb,
        minimum=0,
    )
    return allowed_types


def validate_rate_limit_config(config: RateLimitConfig) -> None:
    """Validate rate-limit defaults."""
    _validate_number(
        field_name="rate_limit.request_delay_min",
        value=config.request_delay_min,
        minimum=0,
    )
    _validate_number(
        field_name="rate_limit.request_delay_max",
        value=config.request_delay_max,
        minimum=0,
    )
    if config.request_delay_max < config.request_delay_min:
        raise InvalidConfigValueError(
            field="rate_limit.request_delay_max",
            value=config.request_delay_max,
            reason="must be greater than or equal to request_delay_min",
        )


def validate_search_defaults_config(config: SearchDefaultsConfig) -> tuple[str, ...]:
    """Validate global search defaults and return normalized search types."""
    _validate_number(
        field_name="defaults.search.limit",
        value=config.limit,
        minimum=1,
        maximum=100,
    )
    return _coerce_tuple(
        field_name="defaults.search.search_types",
        value=config.search_types,
        supported=api_defaults.SUPPORTED_SEARCH_TYPES,
        value_label="search type strings",
    )


def validate_subreddit_search_defaults_config(
    config: SubredditSearchDefaultsConfig,
) -> tuple[str, tuple[str, ...]]:
    """Validate subreddit search defaults."""
    _validate_number(
        field_name="defaults.subreddit_search.limit",
        value=config.limit,
        minimum=1,
        maximum=100,
    )
    sort = _validate_member(
        field_name="defaults.subreddit_search.sort",
        value=config.sort,
        supported=api_defaults.SUPPORTED_SUBREDDIT_SORTS,
    )
    search_types = _coerce_tuple(
        field_name="defaults.subreddit_search.search_types",
        value=config.search_types,
        supported=api_defaults.SUPPORTED_SEARCH_TYPES,
        value_label="search type strings",
    )
    return sort, search_types


def validate_feed_defaults_config(config: FeedDefaultsConfig) -> tuple[str, str]:
    """Validate global feed defaults."""
    _validate_number(
        field_name="defaults.feed.limit",
        value=config.limit,
        minimum=1,
        maximum=100,
    )
    category = _validate_member(
        field_name="defaults.feed.category",
        value=config.category,
        supported=api_defaults.SUPPORTED_GLOBAL_CATEGORIES,
    )
    time_filter = _validate_member(
        field_name="defaults.feed.time_filter",
        value=config.time_filter,
        supported=api_defaults.SUPPORTED_TIME_FILTERS,
    )
    return category, time_filter


def validate_popular_feed_defaults_config(
    config: PopularFeedDefaultsConfig,
) -> tuple[str, str, str | None]:
    """Validate popular-feed defaults."""
    _validate_number(
        field_name="defaults.popular_feed.limit",
        value=config.limit,
        minimum=1,
        maximum=100,
    )
    category = _validate_member(
        field_name="defaults.popular_feed.category",
        value=config.category,
        supported=api_defaults.SUPPORTED_GLOBAL_CATEGORIES,
    )
    time_filter = _validate_member(
        field_name="defaults.popular_feed.time_filter",
        value=config.time_filter,
        supported=api_defaults.SUPPORTED_TIME_FILTERS,
    )
    geo_filter = config.geo_filter
    if geo_filter is not None:
        geo_filter = _validate_member(
            field_name="defaults.popular_feed.geo_filter",
            value=geo_filter.lower(),
            supported=api_defaults.SUPPORTED_GEO_FILTERS,
        )
    return category, time_filter, geo_filter


def validate_subreddit_posts_defaults_config(
    config: SubredditPostsDefaultsConfig,
) -> tuple[str, str]:
    """Validate subreddit/user feed defaults."""
    _validate_number(
        field_name="defaults.subreddit_posts.limit",
        value=config.limit,
        minimum=1,
        maximum=100,
    )
    category = _validate_member(
        field_name="defaults.subreddit_posts.category",
        value=config.category,
        supported=api_defaults.SUPPORTED_SUBREDDIT_CATEGORIES,
    )
    time_filter = _validate_member(
        field_name="defaults.subreddit_posts.time_filter",
        value=config.time_filter,
        supported=api_defaults.SUPPORTED_TIME_FILTERS,
    )
    return category, time_filter


def validate_user_data_defaults_config(config: UserDataDefaultsConfig) -> None:
    """Validate user-data defaults."""
    _validate_number(
        field_name="defaults.user_data.limit",
        value=config.limit,
        minimum=1,
        maximum=100,
    )


def validate_defaults_config(config: DefaultsConfig) -> None:
    """Validate all public operation default bundles."""
    validate_search_defaults_config(config.search)
    validate_subreddit_search_defaults_config(config.subreddit_search)
    validate_feed_defaults_config(config.feed)
    validate_popular_feed_defaults_config(config.popular_feed)
    validate_subreddit_posts_defaults_config(config.subreddit_posts)
    validate_user_data_defaults_config(config.user_data)


def validate_config(config: RedditScraperConfig) -> None:
    """Validate one runtime config snapshot."""
    validate_network_config(config.network)
    validate_cache_config(config.cache)
    validate_media_download_config(config.media)
    validate_rate_limit_config(config.rate_limit)
    validate_defaults_config(config.defaults)
