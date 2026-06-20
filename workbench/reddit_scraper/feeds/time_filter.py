# %%
"""Workbench scenario: subreddit listing time filter.

Why:
    Proves that a top-post subreddit listing accepts a time filter through the
    direct Reddit listing endpoint.

Covers:
    Area: feeds
    Behavior: time-filtered subreddit top posts
    Interface: live `r/<subreddit>/top.json` request with `t=week`

Checks:
    If the time-filtered top listing returns posts, then the count is positive.
    If a sample is present, then it keeps title and permalink evidence.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.feeds.time_filter
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.feeds.time_filter
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

SUBREDDIT = "marvelstudios"
POSTS_LIMIT = 3
CATEGORY = "top"
TIME_FILTER = "week"


# =============================================================================
# Helpers
# =============================================================================


def _fetch_time_filtered_posts(
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch the one time-filtered subreddit listing this scenario owns."""
    payload = fetch_json(
        _subreddit_listing_url(SUBREDDIT, CATEGORY),
        params={"limit": POSTS_LIMIT, "raw_json": 1, "t": TIME_FILTER},
        timeout=timeout,
        proxy=proxy,
    )
    return _posts_from_listing(payload)


def _subreddit_listing_url(subreddit: str, category: str) -> str:
    """Build a subreddit listing URL for the configured category."""
    return f"{REDDIT_BASE_URL}/r/{subreddit}/{category}.json"


def _posts_from_listing(payload: object) -> list[dict[str, Any]]:
    """Normalize post children returned by this time-filter scenario."""
    posts: list[dict[str, Any]] = []
    for child in listing_children(payload):
        data = child.get("data", {})
        if isinstance(data, dict):
            posts.append(normalize_post(data))
    return posts


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, proxy: str | None = None) -> dict[str, Any]:
    """Run one time-filtered top-post listing."""
    posts = _fetch_time_filtered_posts(proxy=proxy)
    first = posts[0] if posts else {}
    return {
        "count": len(posts),
        "sample": {
            "title": first.get("title"),
            "subreddit": first.get("subreddit"),
            "permalink": first.get("permalink") or first.get("link"),
        },
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
        "Fetching weekly top posts from a subreddit.",
        details=(
            f"subreddit: r/{SUBREDDIT}",
            f"category: {CATEGORY}",
            f"time_filter: {TIME_FILTER}",
            f"limit: {POSTS_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    sample = evidence["sample"]
    console.demo_step(
        "Observed Time-Filtered Listing",
        "The listing returned count and first-post evidence.",
        details=(
            f"result count: {evidence['count']}",
            f"first title: {sample.get('title')}",
            f"first permalink: {sample.get('permalink')}",
        ),
    )
    console.print(evidence)
    if evidence["count"] <= 0:
        msg = "Expected the time-filtered subreddit listing to return posts."
        raise RuntimeError(msg)
    console.demo_outcome("The time filter produced a valid live listing.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "count": 3,
  "sample": {"permalink": "/r/...", "subreddit": "marvelstudios", "title": "..."}
}
""".strip()
