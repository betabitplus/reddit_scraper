"""Post-details parsing helpers for reddit_scraper."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from py_lib_runtime import get_logger

from reddit_scraper._api.errors import RedditScraperUnexpectedResponseError
from reddit_scraper._internal.components.utils import MIN_POST_DETAIL_BLOCKS

logger = get_logger(__name__)


def parse_post_details(
    data: list[dict[str, Any]] | None,
    *,
    permalink: str,
    url: str,
    extract_comments: Callable[[list[object]], list[dict[str, Any]]],
) -> dict[str, Any] | None:
    """Parse post details and comments from a Reddit response."""
    if data is None:
        return None
    if len(data) < MIN_POST_DETAIL_BLOCKS:
        raise RedditScraperUnexpectedResponseError(
            url=url,
            reason="expected a list with at least two blocks",
        )

    main_post = data[0]["data"]["children"][0]["data"]
    title = main_post["title"]
    body = main_post.get("selftext", "")
    comments = extract_comments(data[1]["data"]["children"])

    logger.info(
        "Successfully scraped post",
        event_type="reddit.post.scrape.succeeded",
        permalink=permalink,
        title=title,
        report={"comment_count": len(comments)},
    )
    return {"title": title, "body": body, "comments": comments}
