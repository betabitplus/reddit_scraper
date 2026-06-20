# %%
"""Workbench scenario: after-cursor pagination.

Why:
    Proves that Reddit listing cursors can drive a second page while preserving
    the same normalized result shape.

Covers:
    Area: feeds
    Behavior: after-cursor pagination for subreddit listings
    Interface: live listing requests with `after`

Checks:
    If the first page exposes an after cursor, then the second page request
    uses that cursor.
    If the second page returns posts, then duplicate-title evidence stays
    visible.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.feeds.after_pagination
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.feeds.after_pagination
"""

from __future__ import annotations

from typing import Any

from py_lib_tooling import console

from workbench.reddit_scraper._reddit_json import (
    DEFAULT_TIMEOUT_SECONDS,
    REDDIT_BASE_URL,
    fetch_json,
    get_proxy,
    listing_after,
    listing_children,
    normalize_post,
)

# =============================================================================
# Scenario
# =============================================================================

SUBREDDIT = "marvelstudios"
POSTS_LIMIT = 3
CATEGORY = "new"


# =============================================================================
# Helpers
# =============================================================================


def _posts_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize post children from one listing page."""
    posts: list[dict[str, Any]] = []
    for child in listing_children(payload):
        data = child.get("data", {})
        if isinstance(data, dict):
            posts.append(normalize_post(data))
    return posts


def _fetch_listing_payload(
    *,
    after: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> dict[str, Any]:
    """Fetch the subreddit listing payload that exposes cursor metadata."""
    params: dict[str, object] = {
        "limit": POSTS_LIMIT,
        "raw_json": 1,
        "t": "all",
    }
    if after:
        params["after"] = after

    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{SUBREDDIT}/{CATEGORY}.json",
        params=params,
        timeout=timeout,
        proxy=proxy,
    )
    return payload if isinstance(payload, dict) else {}


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, proxy: str | None = None) -> dict[str, Any]:
    """Run a two-page listing cursor probe."""
    page1_payload = _fetch_listing_payload(proxy=proxy)
    page1 = _posts_from_payload(page1_payload)
    after = listing_after(page1_payload)
    page2: list[dict[str, Any]] = []
    if after:
        page2_payload = _fetch_listing_payload(after=after, proxy=proxy)
        page2 = _posts_from_payload(page2_payload)
    duplicates = {post.get("title") for post in page1} & {
        post.get("title") for post in page2
    }
    return {
        "page1_count": len(page1),
        "after_cursor_present": after is not None,
        "page2_count": len(page2),
        "duplicate_titles_count": len(duplicates),
        "page1_first": (page1[0] if page1 else {}).get("title"),
        "page2_first": (page2[0] if page2 else {}).get("title"),
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
        "Fetching a subreddit listing page, then using its after cursor.",
        details=(
            f"subreddit: r/{SUBREDDIT}",
            f"category: {CATEGORY}",
            f"limit: {POSTS_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    console.demo_step(
        "Observed Cursor Evidence",
        "The second page uses Reddit's returned cursor when one is present.",
        details=(
            f"after cursor present: {evidence['after_cursor_present']}",
            f"page 1 count: {evidence['page1_count']}",
            f"page 2 count: {evidence['page2_count']}",
            f"page 1 first title: {evidence['page1_first']}",
            f"page 2 first title: {evidence['page2_first']}",
            f"duplicate titles across pages: {evidence['duplicate_titles_count']}",
        ),
    )
    console.print(evidence)
    if not evidence["after_cursor_present"]:
        msg = "Expected Reddit to return an after cursor for the first page."
        raise RuntimeError(msg)
    console.demo_outcome("Cursor pagination produced second-page evidence.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "after_cursor_present": true,
  "duplicate_titles_count": 0,
  "page1_count": 3,
  "page2_count": 3
}
""".strip()
