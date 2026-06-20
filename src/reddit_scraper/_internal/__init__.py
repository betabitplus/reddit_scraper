"""Private runtime implementation for reddit_scraper.

Why:
    Gives `_api` one private-root import seam while keeping implementation
    modules underscore-scoped and unsupported for callers.
"""

from reddit_scraper._internal.components.resolver import (
    get_default_reddit_scraper_resolver as get_default_reddit_scraper_resolver,
)
from reddit_scraper._internal.config import (
    DefaultsConfig as DefaultsConfig,
    FeedDefaultsConfig as FeedDefaultsConfig,
    MediaDownloadConfig as MediaDownloadConfig,
    NetworkConfig as NetworkConfig,
    PopularFeedDefaultsConfig as PopularFeedDefaultsConfig,
    RateLimitConfig as RateLimitConfig,
    RedditCacheConfig as RedditCacheConfig,
    RedditScraperConfig as RedditScraperConfig,
    SearchDefaultsConfig as SearchDefaultsConfig,
    SubredditPostsDefaultsConfig as SubredditPostsDefaultsConfig,
    SubredditSearchDefaultsConfig as SubredditSearchDefaultsConfig,
    UserDataDefaultsConfig as UserDataDefaultsConfig,
    get_reddit_scraper_config as get_reddit_scraper_config,
    install_reddit_scraper_config as install_reddit_scraper_config,
)
from reddit_scraper._internal.media_downloader.service import (
    MediaDownloader as MediaDownloader,
)
from reddit_scraper._internal.scraper.service import (
    RedditScraper as RedditScraper,
    ScraperConfig as ScraperConfig,
    close_default_reddit_scraper_service as close_default_reddit_scraper_service,
    get_reddit_scraper_service as get_reddit_scraper_service,
)
