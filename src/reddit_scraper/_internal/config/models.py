"""Runtime configuration models.

Why:
    Defines immutable config snapshots consumed by the private runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from reddit_scraper._api import defaults as api_defaults
from reddit_scraper._api.types import MediaConfig
from reddit_scraper._internal.config.validation import (
    validate_cache_config,
    validate_config,
    validate_feed_defaults_config,
    validate_media_download_config,
    validate_network_config,
    validate_popular_feed_defaults_config,
    validate_rate_limit_config,
    validate_search_defaults_config,
    validate_subreddit_posts_defaults_config,
    validate_subreddit_search_defaults_config,
    validate_user_data_defaults_config,
)


@dataclass(frozen=True, slots=True)
class NetworkConfig:
    """Network and retry defaults."""

    timeout_seconds: float = api_defaults.DEFAULT_NETWORK_TIMEOUT_SECONDS
    max_retries: int = api_defaults.DEFAULT_NETWORK_MAX_RETRIES
    random_user_agent: bool = api_defaults.DEFAULT_NETWORK_RANDOM_USER_AGENT

    def __post_init__(self) -> None:
        """Validate network defaults before request setup uses them."""
        validate_network_config(self)


@dataclass(frozen=True, slots=True)
class RedditCacheConfig:
    """Cache defaults for Reddit API responses."""

    enabled: bool = api_defaults.DEFAULT_CACHE_ENABLED
    max_size_mb: float = api_defaults.DEFAULT_CACHE_MAX_SIZE_MB
    cache_dir: str | None = api_defaults.DEFAULT_CACHE_DIR

    def __post_init__(self) -> None:
        """Validate cache defaults before cache managers consume them."""
        validate_cache_config(self)


@dataclass(frozen=True, slots=True)
class MediaDownloadConfig:
    """Defaults for media downloading in reddit_scraper."""

    enabled: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_ENABLED
    allowed_types: tuple[str, ...] = api_defaults.DEFAULT_MEDIA_DOWNLOAD_ALLOWED_TYPES
    max_file_size_mb: float = api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_FILE_SIZE_MB
    max_downloads_per_post: int = (
        api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_DOWNLOADS_PER_POST
    )
    max_total_downloads: int = api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_TOTAL_DOWNLOADS
    cache_media: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_CACHE_MEDIA
    download_thumbnails: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_DOWNLOAD_THUMBNAILS
    skip_head: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_SKIP_HEAD
    use_proxy_for_small: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_SMALL
    use_proxy_for_large: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_LARGE
    proxy_size_threshold_mb: float = (
        api_defaults.DEFAULT_MEDIA_DOWNLOAD_PROXY_SIZE_THRESHOLD_MB
    )
    cache_dir: str | None = api_defaults.DEFAULT_MEDIA_DOWNLOAD_CACHE_DIR

    def __post_init__(self) -> None:
        """Validate media defaults before downloader setup uses them."""
        object.__setattr__(
            self,
            "allowed_types",
            validate_media_download_config(self),
        )

    def to_media_config(self) -> MediaConfig:
        """Convert config DTO to MediaConfig for runtime usage."""
        return MediaConfig(
            enabled=self.enabled,
            allowed_types=self.allowed_types,
            max_file_size_mb=self.max_file_size_mb,
            max_downloads_per_post=self.max_downloads_per_post,
            max_total_downloads=self.max_total_downloads,
            cache_media=self.cache_media,
            download_thumbnails=self.download_thumbnails,
            skip_head=self.skip_head,
            use_proxy_for_small=self.use_proxy_for_small,
            use_proxy_for_large=self.use_proxy_for_large,
            proxy_size_threshold_mb=self.proxy_size_threshold_mb,
        )


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """Rate-limiting defaults for API calls."""

    request_delay_min: float = api_defaults.DEFAULT_RATE_LIMIT_REQUEST_DELAY_MIN
    request_delay_max: float = api_defaults.DEFAULT_RATE_LIMIT_REQUEST_DELAY_MAX

    def __post_init__(self) -> None:
        """Ensure the delay window is valid."""
        validate_rate_limit_config(self)


@dataclass(frozen=True, slots=True)
class SearchDefaultsConfig:
    """Default parameters for global Reddit search."""

    limit: int = api_defaults.DEFAULT_SEARCH_LIMIT
    search_types: tuple[str, ...] = api_defaults.DEFAULT_SEARCH_TYPES

    def __post_init__(self) -> None:
        """Validate global search defaults."""
        object.__setattr__(
            self,
            "search_types",
            validate_search_defaults_config(self),
        )


@dataclass(frozen=True, slots=True)
class SubredditSearchDefaultsConfig:
    """Default parameters for subreddit search."""

    limit: int = api_defaults.DEFAULT_SUBREDDIT_SEARCH_LIMIT
    sort: str = api_defaults.DEFAULT_SUBREDDIT_SEARCH_SORT
    search_types: tuple[str, ...] = api_defaults.DEFAULT_SUBREDDIT_SEARCH_TYPES

    def __post_init__(self) -> None:
        """Validate subreddit search defaults."""
        sort, search_types = validate_subreddit_search_defaults_config(self)
        object.__setattr__(self, "sort", sort)
        object.__setattr__(self, "search_types", search_types)


@dataclass(frozen=True, slots=True)
class FeedDefaultsConfig:
    """Default parameters for global feeds."""

    limit: int = api_defaults.DEFAULT_FEED_LIMIT
    category: str = api_defaults.DEFAULT_FEED_CATEGORY
    time_filter: str = api_defaults.DEFAULT_FEED_TIME_FILTER

    def __post_init__(self) -> None:
        """Validate global feed defaults."""
        category, time_filter = validate_feed_defaults_config(self)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "time_filter", time_filter)


@dataclass(frozen=True, slots=True)
class PopularFeedDefaultsConfig:
    """Default parameters for r/popular feeds."""

    limit: int = api_defaults.DEFAULT_POPULAR_FEED_LIMIT
    category: str = api_defaults.DEFAULT_POPULAR_FEED_CATEGORY
    time_filter: str = api_defaults.DEFAULT_POPULAR_FEED_TIME_FILTER
    geo_filter: str | None = api_defaults.DEFAULT_POPULAR_FEED_GEO_FILTER

    def __post_init__(self) -> None:
        """Validate popular-feed defaults."""
        category, time_filter, geo_filter = validate_popular_feed_defaults_config(self)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "time_filter", time_filter)
        object.__setattr__(self, "geo_filter", geo_filter)


@dataclass(frozen=True, slots=True)
class SubredditPostsDefaultsConfig:
    """Default parameters for subreddit/user feeds."""

    limit: int = api_defaults.DEFAULT_SUBREDDIT_POSTS_LIMIT
    category: str = api_defaults.DEFAULT_SUBREDDIT_POSTS_CATEGORY
    time_filter: str = api_defaults.DEFAULT_SUBREDDIT_POSTS_TIME_FILTER

    def __post_init__(self) -> None:
        """Validate subreddit/user feed defaults."""
        category, time_filter = validate_subreddit_posts_defaults_config(self)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "time_filter", time_filter)


@dataclass(frozen=True, slots=True)
class UserDataDefaultsConfig:
    """Default parameters for user scraping."""

    limit: int = api_defaults.DEFAULT_USER_DATA_LIMIT

    def __post_init__(self) -> None:
        """Validate user-data defaults."""
        validate_user_data_defaults_config(self)


@dataclass(frozen=True, slots=True)
class DefaultsConfig:
    """Default parameter bundles for the public API."""

    search: SearchDefaultsConfig = field(default_factory=SearchDefaultsConfig)
    subreddit_search: SubredditSearchDefaultsConfig = field(
        default_factory=SubredditSearchDefaultsConfig,
    )
    feed: FeedDefaultsConfig = field(default_factory=FeedDefaultsConfig)
    popular_feed: PopularFeedDefaultsConfig = field(
        default_factory=PopularFeedDefaultsConfig,
    )
    subreddit_posts: SubredditPostsDefaultsConfig = field(
        default_factory=SubredditPostsDefaultsConfig,
    )
    user_data: UserDataDefaultsConfig = field(default_factory=UserDataDefaultsConfig)


@dataclass(frozen=True, slots=True)
class RedditScraperConfig:
    """Validated, runtime-ready reddit_scraper configuration."""

    network: NetworkConfig = field(default_factory=NetworkConfig)
    cache: RedditCacheConfig = field(default_factory=RedditCacheConfig)
    media: MediaDownloadConfig = field(default_factory=MediaDownloadConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)

    def __post_init__(self) -> None:
        """Validate the full config snapshot after construction."""
        validate_config(self)
