"""Runtime configuration package.

Why:
    Owns validated immutable configuration snapshots for private scraper
    instances.

What belongs here:
    Config dataclasses, default assembly, validation, and process-wide snapshot
    state.

What does not belong here:
    Public facade helpers, request execution logic, or media download runtime.
"""

from reddit_scraper._internal.config.assembly import (
    build_default_config as build_default_config,
)
from reddit_scraper._internal.config.models import (
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
)
from reddit_scraper._internal.config.state import (
    get_reddit_scraper_config as get_reddit_scraper_config,
    install_reddit_scraper_config as install_reddit_scraper_config,
)
from reddit_scraper._internal.config.validation import (
    validate_config as validate_config,
)
