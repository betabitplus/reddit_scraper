# %%
"""Workbench scenario: post detail comment extraction.

Why:
    Proves that a discovered Reddit permalink can be fetched as a post detail
    document with nested comments.

Covers:
    Area: post details
    Behavior: permalink resolution and nested comment extraction
    Interface: live search/listing plus `<permalink>.json` request

Checks:
    If a permalink is found, then post detail evidence includes a title.
    If comments are returned, then recursive comment count and top-author
    evidence are visible.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.post_details.comment_extraction
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.post_details.comment_extraction
"""

from __future__ import annotations

from typing import Any

from py_lib_tooling import console

from workbench.reddit_scraper._reddit_json import (
    DEFAULT_TIMEOUT_SECONDS,
    REDDIT_BASE_URL,
    fetch_json,
    get_proxy,
    listing_children,
    normalize_post,
)

# =============================================================================
# Scenario
# =============================================================================

SEARCH_QUERY = "Avengers Doomsday trailer"
SEARCH_LIMIT = 1
FALLBACK_SUBREDDIT = "marvelstudios"
FALLBACK_CATEGORY = "hot"
FALLBACK_LIMIT = 1


# =============================================================================
# Helpers
# =============================================================================


def _discover_permalink(*, proxy: str | None) -> str | None:
    """Find one permalink by search, then by fallback listing."""
    results = _search_posts(proxy=proxy)
    if results:
        permalink = results[0].get("permalink")
        if isinstance(permalink, str) and permalink:
            return permalink

    fallback_posts = _fetch_fallback_posts(proxy=proxy)
    if not fallback_posts:
        return None
    permalink = fallback_posts[0].get("permalink")
    return permalink if isinstance(permalink, str) and permalink else None


def _search_posts(
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Search for one post that can provide a comment permalink."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/search.json",
        params={
            "limit": SEARCH_LIMIT,
            "q": SEARCH_QUERY,
            "raw_json": 1,
            "sort": "relevance",
            "type": "link",
        },
        timeout=timeout,
        proxy=proxy,
    )
    return _post_results_from_search(payload)


def _fetch_fallback_posts(
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch the fallback listing used only for permalink discovery."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{FALLBACK_SUBREDDIT}/{FALLBACK_CATEGORY}.json",
        params={"limit": FALLBACK_LIMIT, "raw_json": 1, "t": "all"},
        timeout=timeout,
        proxy=proxy,
    )
    return _posts_from_listing(payload)


def _fetch_post_details(
    permalink: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> dict[str, Any] | None:
    """Fetch the detail document for the discovered permalink."""
    clean_permalink = permalink.removesuffix(".json")
    if not clean_permalink.startswith("/"):
        clean_permalink = f"/{clean_permalink}"

    payload = fetch_json(
        f"{REDDIT_BASE_URL}{clean_permalink}.json",
        params={"raw_json": 1},
        timeout=timeout,
        proxy=proxy,
    )
    if not isinstance(payload, list) or len(payload) < 2:
        return None

    post_children = listing_children(payload[0])
    if not post_children:
        return None
    post_data = post_children[0].get("data", {})
    if not isinstance(post_data, dict):
        return None

    return {
        "title": post_data.get("title", ""),
        "body": post_data.get("selftext", ""),
        "comments": _extract_comments(listing_children(payload[1])),
    }


def _post_results_from_search(payload: object) -> list[dict[str, Any]]:
    """Normalize post search results for permalink discovery."""
    results: list[dict[str, Any]] = []
    for child in listing_children(payload):
        if child.get("kind") != "t3":
            continue
        data = child.get("data", {})
        if isinstance(data, dict):
            result = normalize_post(data)
            result["type"] = "post"
            results.append(result)
    return results


def _posts_from_listing(payload: object) -> list[dict[str, Any]]:
    """Normalize fallback listing post children."""
    posts: list[dict[str, Any]] = []
    for child in listing_children(payload):
        data = child.get("data", {})
        if isinstance(data, dict):
            posts.append(normalize_post(data))
    return posts


def _extract_comments(children: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract nested comments from the detail payload."""
    comments: list[dict[str, Any]] = []
    for child in children:
        if child.get("kind") != "t1":
            continue
        data = child.get("data", {})
        if not isinstance(data, dict):
            continue

        replies: list[dict[str, Any]] = []
        raw_replies = data.get("replies")
        if isinstance(raw_replies, dict):
            replies = _extract_comments(listing_children(raw_replies))

        comments.append(
            {
                "author": data.get("author", ""),
                "body": data.get("body", ""),
                "score": data.get("score", 0),
                "replies": replies,
            }
        )
    return comments


def _count_comments(comments: list[dict[str, Any]]) -> int:
    """Count nested comments and replies for this scenario's evidence."""
    total = 0
    for comment in comments:
        total += 1
        replies = comment.get("replies", [])
        if isinstance(replies, list):
            total += _count_comments(replies)
    return total


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, proxy: str | None = None) -> dict[str, Any]:
    """Run permalink discovery and comment extraction."""
    permalink = _discover_permalink(proxy=proxy)
    if permalink is None:
        return {"found": False}

    details = _fetch_post_details(permalink, proxy=proxy)
    if details is None:
        return {"found": False, "permalink": permalink}

    comments = details.get("comments", [])
    if not isinstance(comments, list):
        comments = []
    return {
        "found": True,
        "permalink": permalink,
        "title": details.get("title"),
        "title_length": len(str(details.get("title", ""))),
        "comment_count": _count_comments(comments),
        "top_authors": [
            comment.get("author") for comment in comments[:3] if comment.get("author")
        ],
    }


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the workbench script as a narrative manual demo."""
    console.demo_intro(__doc__)
    proxy = get_proxy()
    console.demo_step(
        "Scenario",
        "Discovering one post permalink, then fetching its comments.",
        details=(
            f"search query: {SEARCH_QUERY}",
            f"fallback: r/{FALLBACK_SUBREDDIT}/{FALLBACK_CATEGORY}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    console.demo_step(
        "Observed Post Details",
        "The permalink detail endpoint returned title and comment evidence.",
        details=(
            f"permalink: {evidence.get('permalink')}",
            f"title: {evidence.get('title')}",
            f"comment count including replies: {evidence.get('comment_count')}",
            f"top-level authors sampled: {evidence.get('top_authors')}",
        ),
    )
    console.print(evidence)
    if not evidence.get("found"):
        msg = "Expected to discover and fetch a post detail payload."
        raise RuntimeError(msg)
    console.demo_outcome("Post details exposed nested comment evidence.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "comment_count": 12,
  "found": true,
  "permalink": "/r/...",
  "title_length": 72,
  "top_authors": ["..."]
}
""".strip()
