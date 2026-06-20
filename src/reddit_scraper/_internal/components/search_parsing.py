"""Search result parsing helpers for reddit_scraper."""

from __future__ import annotations

from typing import Any

from py_lib_runtime import get_logger

logger = get_logger(__name__)


def parse_search_result(kind: str, item_data: dict[str, Any]) -> dict[str, Any]:
    """Parse search result based on its type (kind)."""
    if kind == "t3":  # Post/Link
        return {
            "type": "post",
            "title": item_data.get("title", ""),
            "link": f"https://www.reddit.com{item_data.get('permalink', '')}",
            "description": item_data.get("selftext", "")[:269],
            "subreddit": item_data.get("subreddit", ""),
            "author": item_data.get("author", ""),
            "score": item_data.get("score", 0),
        }
    if kind == "t1":  # Comment
        return {
            "type": "comment",
            "title": item_data.get("link_title", ""),
            "link": f"https://www.reddit.com{item_data.get('permalink', '')}",
            "body": item_data.get("body", "")[:269],
            "subreddit": item_data.get("subreddit", ""),
            "author": item_data.get("author", ""),
            "score": item_data.get("score", 0),
        }
    if kind == "t5":  # Subreddit
        return {
            "type": "subreddit",
            "title": item_data.get(
                "display_name_prefixed", item_data.get("display_name", "")
            ),
            "link": f"https://www.reddit.com{item_data.get('url', '')}",
            "description": item_data.get("public_description", "")[:269],
            "subscribers": item_data.get("subscribers", 0),
        }
    if kind == "t2":  # User/Account
        return {
            "type": "user",
            "title": f"u/{item_data.get('name', '')}",
            "link": f"https://www.reddit.com/user/{item_data.get('name', '')}",
            "description": "",
        }
    return {
        "type": kind,
        "title": item_data.get("title", item_data.get("name", "Unknown")),
        "link": item_data.get("url", ""),
    }


def handle_search_results(
    data: dict[str, Any],
    *,
    query: str | None,
) -> list[dict[str, Any]]:
    """Parse Reddit search response into normalized results."""
    results: list[dict[str, Any]] = []
    for item in data["data"]["children"]:
        kind = item.get("kind", "")
        item_data = item["data"]
        result = parse_search_result(kind, item_data)
        if result:
            results.append(result)

    logger.info(
        "Search results returned",
        event_type="reddit.search.results.succeeded",
        query=query,
        report={"count": len(results)},
    )
    return results
