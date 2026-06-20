"""Standalone Reddit scraper public API.

Why:
    Exposes the supported library surface while keeping runtime implementation
    under private packages.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from reddit_scraper._api.config import (
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
    get_reddit_scraper_config,
    install_reddit_scraper_config,
)
from reddit_scraper._api.errors import (
    InvalidConfigValueError,
    RedditScraperConfigurationError,
    RedditScraperError,
    RedditScraperProviderError,
    RedditScraperRateLimitError,
    RedditScraperRequestError,
    RedditScraperResponseParseError,
    RedditScraperUnexpectedResponseError,
    RedditScraperUsageError,
    RedditScraperValidationError,
)
from reddit_scraper._api.scraper import (
    MediaDownloader,
    RedditScraper,
    ScraperConfig,
    close_default_scraper,
    download_media,
    fetch_all,
    fetch_frontpage,
    fetch_popular,
    fetch_subreddit_posts,
    get_default_media_config,
    scrape_post_details,
    scrape_user_data,
    search_reddit,
    search_subreddit,
)
from reddit_scraper._api.types import (
    ClientOptions,
    FeedOptions,
    GeoFilter,
    MediaConfig,
    MediaDownloadResponse,
    MediaItem,
    MediaType,
    PopularFeedOptions,
    PostDetailsResponse,
    RedditCacheEntry,
    SearchOptions,
    SearchResponse,
    SearchType,
    SortCategory,
    SubredditPostsOptions,
    SubredditSearchOptions,
    TimeFilter,
    UserDataResponse,
)

try:
    __version__ = version("reddit-scraper")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "ClientOptions",
    "DefaultsConfig",
    "FeedDefaultsConfig",
    "FeedOptions",
    "GeoFilter",
    "InvalidConfigValueError",
    "MediaConfig",
    "MediaDownloadConfig",
    "MediaDownloadResponse",
    "MediaDownloader",
    "MediaItem",
    "MediaType",
    "NetworkConfig",
    "PopularFeedDefaultsConfig",
    "PopularFeedOptions",
    "PostDetailsResponse",
    "RateLimitConfig",
    "RedditCacheConfig",
    "RedditCacheEntry",
    "RedditScraper",
    "RedditScraperConfig",
    "RedditScraperConfigurationError",
    "RedditScraperError",
    "RedditScraperProviderError",
    "RedditScraperRateLimitError",
    "RedditScraperRequestError",
    "RedditScraperResponseParseError",
    "RedditScraperUnexpectedResponseError",
    "RedditScraperUsageError",
    "RedditScraperValidationError",
    "ScraperConfig",
    "SearchDefaultsConfig",
    "SearchOptions",
    "SearchResponse",
    "SearchType",
    "SortCategory",
    "SubredditPostsDefaultsConfig",
    "SubredditPostsOptions",
    "SubredditSearchDefaultsConfig",
    "SubredditSearchOptions",
    "TimeFilter",
    "UserDataDefaultsConfig",
    "UserDataResponse",
    "close_default_scraper",
    "download_media",
    "fetch_all",
    "fetch_frontpage",
    "fetch_popular",
    "fetch_subreddit_posts",
    "get_default_media_config",
    "get_reddit_scraper_config",
    "install_reddit_scraper_config",
    "scrape_post_details",
    "scrape_user_data",
    "search_reddit",
    "search_subreddit",
]
