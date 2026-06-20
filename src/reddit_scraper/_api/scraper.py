"""Thin public scraper operations for the root package API."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from reddit_scraper._api.config import get_reddit_scraper_config
from reddit_scraper._api.types import (
    ClientOptions,
    FeedOptions,
    MediaConfig,
    MediaDownloadResponse,
    PopularFeedOptions,
    PostDetailsResponse,
    SearchOptions,
    SearchResponse,
    SubredditPostsOptions,
    SubredditSearchOptions,
    UserDataResponse,
)
from reddit_scraper._internal import (
    MediaDownloader,
    RedditScraper as _RedditScraperService,
    ScraperConfig as _ScraperConfig,
    close_default_reddit_scraper_service,
    get_default_reddit_scraper_resolver,
    get_reddit_scraper_service,
)

RedditScraper = _RedditScraperService
ScraperConfig = _ScraperConfig


# =============================================================================
# Public Operations
# =============================================================================


def search_reddit(
    query: str,
    *,
    options: SearchOptions | None = None,
    client: ClientOptions | None = None,
) -> SearchResponse:
    """Search Reddit globally.

    Args:
        query: Search query string
        options: Optional search options (limit, cursors, search types)
        client: Optional client options (proxy, timeout, cache)

    Returns:
        SearchResponse with results and metadata
    """
    resolver = get_default_reddit_scraper_resolver()
    options = resolver.resolve_search_options(options)
    scraper = get_reddit_scraper_service(client=client)
    results = scraper.search_reddit(
        query=query,
        options=options,
    )
    return SearchResponse(
        results=results,
        metadata={
            "query": query,
            "limit": options.limit,
            "search_types": options.search_types,
        },
    )


def search_subreddit(
    subreddit: str,
    query: str,
    *,
    options: SubredditSearchOptions | None = None,
    client: ClientOptions | None = None,
) -> SearchResponse:
    """Search within a specific subreddit.

    Args:
        subreddit: Subreddit name (without r/)
        query: Search query string
        options: Optional search options (limit, cursors, sort, types)
        client: Optional client options (proxy, timeout, cache)

    Returns:
        SearchResponse with results and metadata
    """
    resolver = get_default_reddit_scraper_resolver()
    options = resolver.resolve_subreddit_search_options(options)
    scraper = get_reddit_scraper_service(client=client)
    results = scraper.search_subreddit(
        subreddit=subreddit,
        query=query,
        options=options,
    )
    return SearchResponse(
        results=results,
        metadata={
            "subreddit": subreddit,
            "query": query,
            "limit": options.limit,
            "sort": options.sort,
        },
    )


def scrape_post_details(
    permalink: str,
    *,
    proxy: str | None = None,
    timeout: float | None = None,
    cache_dir: str | None = None,
) -> PostDetailsResponse | None:
    """Get post details with comments.

    Args:
        permalink: Post permalink (e.g., /r/python/comments/abc123/...)
        proxy: Optional proxy URL
        timeout: Request timeout in seconds
        cache_dir: Directory for API cache storage (disabled if None)

    Returns:
        PostDetailsResponse with title, body, and comments, or None if failed
    """
    scraper = get_reddit_scraper_service(
        client=ClientOptions(proxy=proxy, timeout=timeout, cache_dir=cache_dir)
    )
    result = scraper.scrape_post_details(permalink)
    if result is None:
        return None
    return PostDetailsResponse(
        title=result["title"],
        body=result["body"],
        comments=result["comments"],
        metadata={"permalink": permalink},
    )


def scrape_user_data(
    username: str,
    *,
    limit: int | None = None,
    proxy: str | None = None,
    timeout: float | None = None,
    cache_dir: str | None = None,
) -> UserDataResponse:
    """Get user profile and activity.

    Args:
        username: Reddit username
        limit: Maximum items to return
        proxy: Optional proxy URL
        timeout: Request timeout in seconds
        cache_dir: Directory for API cache storage (disabled if None)

    Returns:
        UserDataResponse with user's posts and comments
    """
    resolver = get_default_reddit_scraper_resolver()
    limit = resolver.resolve_user_limit(limit)
    scraper = get_reddit_scraper_service(
        client=ClientOptions(proxy=proxy, timeout=timeout, cache_dir=cache_dir)
    )
    items = scraper.scrape_user_data(username=username, limit=limit)
    return UserDataResponse(
        items=items,
        metadata={"username": username, "limit": limit},
    )


def fetch_frontpage(
    *,
    options: FeedOptions | None = None,
    client: ClientOptions | None = None,
) -> SearchResponse:
    """Fetch posts from Reddit frontpage.

    Args:
        options: Optional feed options (limit, category, time filter)
        client: Optional client options (proxy, timeout, cache)

    Returns:
        SearchResponse with frontpage posts
    """
    resolver = get_default_reddit_scraper_resolver()
    options = resolver.resolve_feed_options(options)
    scraper = get_reddit_scraper_service(client=client)
    results = scraper.fetch_frontpage(options=options)
    return SearchResponse(
        results=results,
        metadata={
            "source": "frontpage",
            "category": options.category,
            "time_filter": options.time_filter,
        },
    )


def fetch_all(
    *,
    options: FeedOptions | None = None,
    client: ClientOptions | None = None,
) -> SearchResponse:
    """Fetch posts from r/all.

    Args:
        options: Optional feed options (limit, category, time filter)
        client: Optional client options (proxy, timeout, cache)

    Returns:
        SearchResponse with r/all posts
    """
    resolver = get_default_reddit_scraper_resolver()
    options = resolver.resolve_feed_options(options)
    scraper = get_reddit_scraper_service(client=client)
    results = scraper.fetch_all(options=options)
    return SearchResponse(
        results=results,
        metadata={
            "source": "all",
            "category": options.category,
            "time_filter": options.time_filter,
        },
    )


def fetch_popular(
    *,
    options: PopularFeedOptions | None = None,
    client: ClientOptions | None = None,
) -> SearchResponse:
    """Fetch posts from r/popular with optional geographic filter.

    Args:
        options: Optional feed options (limit, category, time filter, geo)
        client: Optional client options (proxy, timeout, cache)

    Returns:
        SearchResponse with r/popular posts
    """
    resolver = get_default_reddit_scraper_resolver()
    options = resolver.resolve_popular_feed_options(options)
    scraper = get_reddit_scraper_service(client=client)
    results = scraper.fetch_popular(options=options)
    return SearchResponse(
        results=results,
        metadata={
            "source": "popular",
            "category": options.category,
            "time_filter": options.time_filter,
            "geo_filter": options.geo_filter,
        },
    )


def fetch_subreddit_posts(
    subreddit: str,
    *,
    options: SubredditPostsOptions | None = None,
    client: ClientOptions | None = None,
) -> SearchResponse:
    """Fetch posts from a subreddit.

    Args:
        subreddit: Subreddit name (without r/)
        options: Optional feed options (limit, category, time filter)
        client: Optional client options (proxy, timeout, cache)

    Returns:
        SearchResponse with subreddit posts
    """
    resolver = get_default_reddit_scraper_resolver()
    options = resolver.resolve_subreddit_posts_options(options)
    scraper = get_reddit_scraper_service(client=client)
    results = scraper.fetch_subreddit_posts(subreddit=subreddit, options=options)
    return SearchResponse(
        results=results,
        metadata={
            "subreddit": subreddit,
            "category": options.category,
            "time_filter": options.time_filter,
        },
    )


def download_media(
    url: str,
    *,
    config: MediaConfig | None = None,
    proxy: str | None = None,
    cache_dir: str | None = None,
) -> MediaDownloadResponse:
    """Download media from a URL.

    Args:
        url: Media URL to download
        config: Media download configuration
        proxy: Optional proxy URL
        cache_dir: Directory for media cache storage (disabled if None)

    Returns:
        MediaDownloadResponse with downloaded items and stats
    """
    if config is None:
        defaults = get_reddit_scraper_config().media
        config = replace(defaults.to_media_config(), enabled=True)

    with MediaDownloader(
        config=config,
        proxy=proxy,
        cache_dir=Path(cache_dir).expanduser() if cache_dir else None,
    ) as downloader:
        item = downloader.download(url)
        items = [item] if item else []
        return MediaDownloadResponse(
            items=items,
            stats=downloader.stats(),
        )


def close_default_scraper() -> None:
    """Close the default scraper instance.

    Call this to release resources when done with function-based API.
    """
    close_default_reddit_scraper_service()


def get_default_media_config() -> MediaConfig:
    """Return the configured default media download settings."""
    return get_reddit_scraper_config().media.to_media_config()
