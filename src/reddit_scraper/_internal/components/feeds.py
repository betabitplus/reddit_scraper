"""Feed operations for the reddit_scraper service.

This module is an internal implementation detail.
"""

from __future__ import annotations

import logging
from typing import Any

from py_lib_runtime import get_logger, log_operation_duration

from reddit_scraper._api.defaults import (
    SUPPORTED_GLOBAL_CATEGORIES,
    SUPPORTED_SUBREDDIT_CATEGORIES,
)
from reddit_scraper._api.errors import (
    RedditScraperUnexpectedResponseError,
    RedditScraperValidationError,
)
from reddit_scraper._api.types import (
    FeedOptions,
    PopularFeedOptions,
    SubredditPostsOptions,
)
from reddit_scraper._internal.components.parsing import get_listing_items
from reddit_scraper._internal.components.resolver import (
    get_default_reddit_scraper_resolver,
)
from reddit_scraper._internal.components.utils import MAX_PAGE_SIZE, sleep_jitter

logger = get_logger(__name__)


def build_global_url(base_url: str, category: str) -> str:
    """Build a Reddit global feed URL for the category."""
    if category == "hot":
        if base_url == "https://www.reddit.com":
            return f"{base_url}/.json"
        return f"{base_url}/hot.json"
    return f"{base_url}/{category}.json"


def build_subreddit_url(subreddit: str, category: str) -> str:
    """Build a subreddit or user feed URL for the category."""
    if category == "hot":
        return f"https://www.reddit.com/r/{subreddit}/hot.json"
    if category == "top":
        return f"https://www.reddit.com/r/{subreddit}/top.json"
    if category == "new":
        return f"https://www.reddit.com/r/{subreddit}/new.json"
    if category == "userhot":
        return f"https://www.reddit.com/user/{subreddit}/submitted/hot.json"
    if category == "usertop":
        return f"https://www.reddit.com/user/{subreddit}/submitted/top.json"
    return f"https://www.reddit.com/user/{subreddit}/submitted/new.json"


def get_after_cursor(data: dict[str, Any]) -> str | None:
    """Return the pagination cursor from a listing response."""
    return data.get("data", {}).get("after")


def validate_global_category(category: str) -> None:
    """Validate category for global feeds."""
    if category not in SUPPORTED_GLOBAL_CATEGORIES:
        raise RedditScraperValidationError(
            field="category",
            value=category,
            reason=f"must be one of {list(SUPPORTED_GLOBAL_CATEGORIES)}",
        )


def validate_subreddit_category(category: str) -> None:
    """Validate category for subreddit or user feeds."""
    if category not in SUPPORTED_SUBREDDIT_CATEGORIES:
        raise RedditScraperValidationError(
            field="category",
            value=category,
            reason=(
                "must be 'hot', 'top', 'new' for subreddits "
                "or 'userhot', 'usertop', 'usernew' for users"
            ),
        )


def extract_post_info(post_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Reddit post payload into a summary dict."""
    post_info = {
        "title": post_data.get("title"),
        "author": post_data.get("author"),
        "subreddit": post_data.get("subreddit"),
        "permalink": post_data.get("permalink"),
        "score": post_data.get("score"),
        "num_comments": post_data.get("num_comments"),
        "created_utc": post_data.get("created_utc"),
    }
    image_url = None
    if post_data.get("post_hint") == "image" and "url" in post_data:
        image_url = post_data["url"]
    elif "preview" in post_data and "images" in post_data.get("preview", {}):
        image_url = post_data["preview"]["images"][0]["source"]["url"]
    if image_url:
        post_info["image_url"] = image_url

    thumbnail = post_data.get("thumbnail")
    if thumbnail and thumbnail not in ["self", "default", "nsfw"]:
        post_info["thumbnail_url"] = thumbnail
    return post_info


def extend_posts(
    posts: list[dict[str, Any]],
    all_posts: list[dict[str, Any]],
    remaining: int,
) -> int:
    """Append post summaries and return how many were added."""
    added = 0
    for post in posts:
        post_data = post.get("data", {})
        if not isinstance(post_data, dict):
            continue
        all_posts.append(extract_post_info(post_data))
        added += 1
        if added >= remaining:
            break
    return added


class FeedMixin:
    """Mixin that provides Reddit feed operations."""

    def fetch_frontpage(
        self,
        *,
        options: FeedOptions | None = None,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch posts from Reddit frontpage."""
        with log_operation_duration(
            logger,
            event_type="reddit.feed.frontpage.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
            feed="frontpage",
        ):
            resolver = get_default_reddit_scraper_resolver()
            options = resolver.resolve_feed_options(options)
            return self._fetch_global_posts(
                base_url="https://www.reddit.com",
                options=options,
                context="frontpage",
            )

    def fetch_all(
        self,
        *,
        options: FeedOptions | None = None,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch posts from r/all."""
        with log_operation_duration(
            logger,
            event_type="reddit.feed.all.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
            feed="all",
        ):
            resolver = get_default_reddit_scraper_resolver()
            options = resolver.resolve_feed_options(options)
            return self._fetch_global_posts(
                base_url="https://www.reddit.com/r/all",
                options=options,
                context="all",
            )

    def fetch_popular(
        self,
        *,
        options: PopularFeedOptions | None = None,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch posts from r/popular with optional geographic filter."""
        with log_operation_duration(
            logger,
            event_type="reddit.feed.popular.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
            feed="popular",
        ):
            resolver = get_default_reddit_scraper_resolver()
            options = resolver.resolve_popular_feed_options(options)
            return self._fetch_global_posts(
                base_url="https://www.reddit.com/r/popular",
                options=options,
                context="popular",
            )

    def _fetch_global_posts(
        self,
        base_url: str,
        *,
        options: FeedOptions | PopularFeedOptions,
        context: str,
    ) -> list[dict[str, Any]]:
        """Internal method to fetch posts from global Reddit feeds."""
        if options.category is None:
            raise RedditScraperValidationError(
                field="category",
                value=options.category,
                reason="is required",
            )
        if options.time_filter is None:
            raise RedditScraperValidationError(
                field="time_filter",
                value=options.time_filter,
                reason="is required",
            )
        if options.limit is None:
            raise RedditScraperValidationError(
                field="limit",
                value=options.limit,
                reason="is required",
            )

        limit = options.limit
        category = options.category
        time_filter = options.time_filter
        validate_global_category(category)

        batch_size = min(MAX_PAGE_SIZE, limit)
        total_fetched = 0
        after: str | None = None
        all_posts: list[dict[str, Any]] = []
        geo_filter = getattr(options, "geo_filter", None)

        while total_fetched < limit:
            url = build_global_url(base_url, category)
            params = {
                "limit": batch_size,
                "after": after,
                "raw_json": 1,
                "t": time_filter,
            }
            if geo_filter:
                params["geo_filter"] = str(geo_filter).lower()

            data = self._fetch_posts_page(
                url,
                params,
                cache_first_page=after is None,
                context=f"{context} posts",
            )
            if data is None:
                break

            posts = get_listing_items(data)
            if not posts:
                break

            remaining = limit - total_fetched
            total_fetched += extend_posts(posts, all_posts, remaining)
            if total_fetched >= limit:
                break

            after = get_after_cursor(data)
            if not after:
                break

            sleep_jitter()

        logger.info(
            "Fetched posts",
            event_type="reddit.feed.fetch.succeeded",
            feed=context,
            report={
                "count": len(all_posts),
                "limit": limit,
            },
        )
        return all_posts

    def fetch_subreddit_posts(
        self,
        subreddit: str,
        *,
        options: SubredditPostsOptions | None = None,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch posts from a subreddit or user feed."""
        with log_operation_duration(
            logger,
            event_type="reddit.subreddit.posts.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
            subreddit=subreddit,
        ):
            resolver = get_default_reddit_scraper_resolver()
            options = resolver.resolve_subreddit_posts_options(options)

            if options.category is None:
                raise RedditScraperValidationError(
                    field="category",
                    value=options.category,
                    reason="is required",
                )

            limit, category, time_filter = self._resolve_subreddit_posts_options(
                options
            )
            logger.debug(
                "Fetching subreddit posts",
                event_type="reddit.subreddit.fetch.started",
                subreddit=subreddit,
                category=category,
                time_filter=time_filter,
                limit=limit,
            )
            return self._fetch_subreddit_posts_pages(
                subreddit=subreddit,
                limit=limit,
                category=category,
                time_filter=time_filter,
            )

    def _resolve_subreddit_posts_options(
        self, options: SubredditPostsOptions
    ) -> tuple[int, str, str]:
        """Validate and normalize subreddit post options."""
        if options.category is None:
            raise RedditScraperValidationError(
                field="category",
                value=options.category,
                reason="is required",
            )
        if options.time_filter is None:
            raise RedditScraperValidationError(
                field="time_filter",
                value=options.time_filter,
                reason="is required",
            )
        if options.limit is None:
            raise RedditScraperValidationError(
                field="limit",
                value=options.limit,
                reason="is required",
            )
        validate_subreddit_category(options.category)
        return options.limit, options.category, options.time_filter

    def _fetch_subreddit_posts_pages(
        self,
        *,
        subreddit: str,
        limit: int,
        category: str,
        time_filter: str,
    ) -> list[dict[str, Any]]:
        """Fetch subreddit posts across paginated requests."""
        batch_size = min(MAX_PAGE_SIZE, limit)
        total_fetched = 0
        after: str | None = None
        all_posts: list[dict[str, Any]] = []

        while total_fetched < limit:
            url = build_subreddit_url(subreddit, category)
            params = {
                "limit": batch_size,
                "after": after,
                "raw_json": 1,
                "t": time_filter,
            }

            data = self._fetch_posts_page(
                url,
                params,
                cache_first_page=after is None,
                context="Subreddit/user posts",
            )
            if data is None:
                break

            posts = get_listing_items(data)
            if not posts:
                break

            remaining = limit - total_fetched
            total_fetched += extend_posts(posts, all_posts, remaining)
            if total_fetched >= limit:
                break

            after = get_after_cursor(data)
            if not after:
                break

            sleep_jitter()
            logger.debug(
                "Sleeping between pagination requests",
                event_type="reddit.subreddit.pagination.sleep.started",
            )

        logger.info(
            "Successfully fetched subreddit posts",
            event_type="reddit.subreddit.fetch.succeeded",
            subreddit=subreddit,
            report={"count": len(all_posts), "limit": limit},
        )
        return all_posts

    def _fetch_posts_page(
        self,
        url: str,
        params: dict[str, Any],
        *,
        cache_first_page: bool,
        context: str,
    ) -> dict[str, Any] | None:
        """Fetch a single page of posts with optional caching."""
        data = self._fetch_json_page(
            url,
            params,
            cache_first_page=cache_first_page,
            context=context,
        )
        if data is None:
            return None
        if not isinstance(data, dict):
            raise RedditScraperUnexpectedResponseError(
                url=url,
                reason="expected a JSON object response",
            )
        return data
