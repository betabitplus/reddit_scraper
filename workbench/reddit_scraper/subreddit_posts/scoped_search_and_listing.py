# %%
"""Workbench scenario: subreddit-scoped search and listing.

Why:
    Proves that subreddit names constrain both search and post-listing requests
    through direct Reddit endpoints.

Covers:
    Area: subreddit posts
    Behavior: subreddit search and hot post listing
    Interface: live subreddit search and listing JSON requests

Checks:
    If scoped searches return results, then each target subreddit has a
    visible result count.
    If hot posts are fetched, then count and permalink evidence are visible.

Examples:
    Run manually:
        uv run python -m \
            workbench.reddit_scraper.subreddit_posts.scoped_search_and_listing
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.subreddit_posts.scoped_search_and_listing
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

TARGET_SUBREDDITS = ("marvelstudios", "Marvel")
SEARCH_QUERY = "Avengers Doomsday"
SEARCH_LIMIT = 3
SEARCH_SORT = "relevance"
HOT_SUBREDDIT = "marvelstudios"
HOT_LIMIT = 3
HOT_CATEGORY = "hot"


# =============================================================================
# Helpers
# =============================================================================


def _search_subreddit(
    subreddit: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Run one scoped search page for this subreddit scenario."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{subreddit}/search.json",
        params={
            "limit": SEARCH_LIMIT,
            "q": SEARCH_QUERY,
            "raw_json": 1,
            "restrict_sr": "on",
            "sort": SEARCH_SORT,
            "type": "link",
        },
        timeout=timeout,
        proxy=proxy,
    )
    return _post_results_from_search(payload)


def _fetch_hot_posts(
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch the hot listing this subreddit scenario owns."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{HOT_SUBREDDIT}/{HOT_CATEGORY}.json",
        params={"limit": HOT_LIMIT, "raw_json": 1, "t": "all"},
        timeout=timeout,
        proxy=proxy,
    )
    return _posts_from_listing(payload)


def _post_results_from_search(payload: object) -> list[dict[str, Any]]:
    """Normalize post search results for scoped subreddit evidence."""
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
    """Normalize post children from the hot listing."""
    posts: list[dict[str, Any]] = []
    for child in listing_children(payload):
        data = child.get("data", {})
        if isinstance(data, dict):
            posts.append(normalize_post(data))
    return posts


def _summarize_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return compact post evidence for this subreddit scenario."""
    return [
        {
            "title": post.get("title"),
            "subreddit": post.get("subreddit"),
            "permalink": post.get("permalink") or post.get("link"),
        }
        for post in posts
    ]


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, proxy: str | None = None) -> dict[str, Any]:
    """Run scoped search and hot listing behavior."""
    search_results = {
        subreddit: _search_subreddit(subreddit, proxy=proxy)
        for subreddit in TARGET_SUBREDDITS
    }
    hot_posts = _fetch_hot_posts(proxy=proxy)
    return {
        "search_counts": {
            subreddit: len(results) for subreddit, results in search_results.items()
        },
        "hot_posts_count": len(hot_posts),
        "hot_samples": _summarize_posts(hot_posts[:2]),
        "first_search_samples": _summarize_posts(
            search_results.get(TARGET_SUBREDDITS[0], [])[:2]
        ),
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
        "Searching inside target subreddits and fetching one hot listing.",
        details=(
            f"target subreddits: {list(TARGET_SUBREDDITS)}",
            f"query: {SEARCH_QUERY}",
            f"hot listing: r/{HOT_SUBREDDIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    hot_samples = evidence["hot_samples"]
    first_search_samples = evidence["first_search_samples"]
    hot_first = hot_samples[0] if hot_samples else {}
    search_first = first_search_samples[0] if first_search_samples else {}
    console.demo_step(
        "Observed Subreddit Evidence",
        "Scoped searches and the hot listing returned separate result buckets.",
        details=(
            f"search counts: {evidence['search_counts']}",
            f"hot post count: {evidence['hot_posts_count']}",
            f"first scoped-search title: {search_first.get('title')}",
            f"first hot title: {hot_first.get('title')}",
            f"first hot permalink: {hot_first.get('permalink')}",
        ),
    )
    console.print(evidence)
    if evidence["hot_posts_count"] <= 0:
        msg = "Expected subreddit hot listing to return posts."
        raise RuntimeError(msg)
    console.demo_outcome("Subreddit-scoped behavior produced live post evidence.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "hot_posts_count": 3,
  "search_counts": {"Marvel": 3, "marvelstudios": 3}
}
""".strip()
