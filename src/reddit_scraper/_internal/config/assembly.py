"""Built-in config assembly.

Why:
    Converts public default declarations into validated private config snapshots
    before runtime work begins.
"""

from __future__ import annotations

from py_lib_runtime import get_logger

from reddit_scraper._api import defaults as api_defaults
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
from reddit_scraper._internal.config.validation import validate_config

logger = get_logger(__name__)


def build_default_config() -> RedditScraperConfig:
    """Assemble and validate the built-in runtime config snapshot."""
    config = RedditScraperConfig(
        network=NetworkConfig(
            timeout_seconds=api_defaults.DEFAULT_NETWORK_TIMEOUT_SECONDS,
            max_retries=api_defaults.DEFAULT_NETWORK_MAX_RETRIES,
            random_user_agent=api_defaults.DEFAULT_NETWORK_RANDOM_USER_AGENT,
        ),
        cache=RedditCacheConfig(
            enabled=api_defaults.DEFAULT_CACHE_ENABLED,
            max_size_mb=api_defaults.DEFAULT_CACHE_MAX_SIZE_MB,
            cache_dir=api_defaults.DEFAULT_CACHE_DIR,
        ),
        media=MediaDownloadConfig(
            enabled=api_defaults.DEFAULT_MEDIA_DOWNLOAD_ENABLED,
            allowed_types=api_defaults.DEFAULT_MEDIA_DOWNLOAD_ALLOWED_TYPES,
            max_file_size_mb=api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_FILE_SIZE_MB,
            max_downloads_per_post=(
                api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_DOWNLOADS_PER_POST
            ),
            max_total_downloads=api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_TOTAL_DOWNLOADS,
            cache_media=api_defaults.DEFAULT_MEDIA_DOWNLOAD_CACHE_MEDIA,
            download_thumbnails=(
                api_defaults.DEFAULT_MEDIA_DOWNLOAD_DOWNLOAD_THUMBNAILS
            ),
            skip_head=api_defaults.DEFAULT_MEDIA_DOWNLOAD_SKIP_HEAD,
            use_proxy_for_small=api_defaults.DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_SMALL,
            use_proxy_for_large=api_defaults.DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_LARGE,
            proxy_size_threshold_mb=(
                api_defaults.DEFAULT_MEDIA_DOWNLOAD_PROXY_SIZE_THRESHOLD_MB
            ),
            cache_dir=api_defaults.DEFAULT_MEDIA_DOWNLOAD_CACHE_DIR,
        ),
        rate_limit=RateLimitConfig(
            request_delay_min=api_defaults.DEFAULT_RATE_LIMIT_REQUEST_DELAY_MIN,
            request_delay_max=api_defaults.DEFAULT_RATE_LIMIT_REQUEST_DELAY_MAX,
        ),
        defaults=DefaultsConfig(
            search=SearchDefaultsConfig(
                limit=api_defaults.DEFAULT_SEARCH_LIMIT,
                search_types=api_defaults.DEFAULT_SEARCH_TYPES,
            ),
            subreddit_search=SubredditSearchDefaultsConfig(
                limit=api_defaults.DEFAULT_SUBREDDIT_SEARCH_LIMIT,
                sort=api_defaults.DEFAULT_SUBREDDIT_SEARCH_SORT,
                search_types=api_defaults.DEFAULT_SUBREDDIT_SEARCH_TYPES,
            ),
            feed=FeedDefaultsConfig(
                limit=api_defaults.DEFAULT_FEED_LIMIT,
                category=api_defaults.DEFAULT_FEED_CATEGORY,
                time_filter=api_defaults.DEFAULT_FEED_TIME_FILTER,
            ),
            popular_feed=PopularFeedDefaultsConfig(
                limit=api_defaults.DEFAULT_POPULAR_FEED_LIMIT,
                category=api_defaults.DEFAULT_POPULAR_FEED_CATEGORY,
                time_filter=api_defaults.DEFAULT_POPULAR_FEED_TIME_FILTER,
                geo_filter=api_defaults.DEFAULT_POPULAR_FEED_GEO_FILTER,
            ),
            subreddit_posts=SubredditPostsDefaultsConfig(
                limit=api_defaults.DEFAULT_SUBREDDIT_POSTS_LIMIT,
                category=api_defaults.DEFAULT_SUBREDDIT_POSTS_CATEGORY,
                time_filter=api_defaults.DEFAULT_SUBREDDIT_POSTS_TIME_FILTER,
            ),
            user_data=UserDataDefaultsConfig(
                limit=api_defaults.DEFAULT_USER_DATA_LIMIT,
            ),
        ),
    )
    validate_config(config)
    logger.info(
        "Runtime config resolved",
        event_type="reddit_scraper.config.runtime.resolved",
        network_timeout_seconds=config.network.timeout_seconds,
        cache_enabled=config.cache.enabled,
        media_enabled=config.media.enabled,
    )
    return config
