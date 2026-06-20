# %%
"""Workbench scenario: global Reddit feed families.

Why:
    Proves that frontpage, r/all, and r/popular listings can be fetched as
    separate live feed buckets without shipped scraper code.

Covers:
    Area: feeds
    Behavior: frontpage, all, and popular listing retrieval
    Interface: live Reddit listing JSON endpoints

Checks:
    If each global feed returns posts, then each feed count is positive.
    If distinct feed options are used, then the evidence keeps each feed bucket
    separate.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.feeds.global_families
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.feeds.global_families
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

FRONTPAGE_LIMIT = 5
FRONTPAGE_CATEGORY = "hot"
ALL_LIMIT = 5
ALL_CATEGORY = "top"
ALL_TIME_FILTER = "day"
POPULAR_LIMIT = 5
POPULAR_CATEGORY = "new"


# =============================================================================
# Helpers
# =============================================================================


def _first_sample(posts: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact sample evidence for one feed."""
    first = posts[0] if posts else {}
    return {
        "title": first.get("title"),
        "subreddit": first.get("subreddit"),
        "permalink": first.get("permalink") or first.get("link"),
    }


def _fetch_global_feed(
    feed: str,
    *,
    limit: int,
    category: str,
    time_filter: str = "all",
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch one global feed bucket for this scenario."""
    base_url = {
        "frontpage": REDDIT_BASE_URL,
        "all": f"{REDDIT_BASE_URL}/r/all",
        "popular": f"{REDDIT_BASE_URL}/r/popular",
    }[feed]
    payload = fetch_json(
        _build_global_url(base_url, category),
        params={"limit": limit, "raw_json": 1, "t": time_filter},
        timeout=DEFAULT_TIMEOUT_SECONDS,
        proxy=proxy,
    )
    return _posts_from_listing(payload)


def _build_global_url(base_url: str, category: str) -> str:
    """Build the live listing URL for one global feed variant."""
    if category == "hot":
        if base_url == REDDIT_BASE_URL:
            return f"{base_url}/.json"
        return f"{base_url}/hot.json"
    return f"{base_url}/{category}.json"


def _posts_from_listing(payload: object) -> list[dict[str, Any]]:
    """Normalize post children returned by this feed scenario."""
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
    """Run the isolated global feed family behavior."""
    frontpage = _fetch_global_feed(
        "frontpage",
        limit=FRONTPAGE_LIMIT,
        category=FRONTPAGE_CATEGORY,
        proxy=proxy,
    )
    all_posts = _fetch_global_feed(
        "all",
        limit=ALL_LIMIT,
        category=ALL_CATEGORY,
        time_filter=ALL_TIME_FILTER,
        proxy=proxy,
    )
    popular = _fetch_global_feed(
        "popular",
        limit=POPULAR_LIMIT,
        category=POPULAR_CATEGORY,
        proxy=proxy,
    )
    return {
        "frontpage_count": len(frontpage),
        "all_count": len(all_posts),
        "popular_count": len(popular),
        "frontpage_sample": _first_sample(frontpage),
        "all_sample": _first_sample(all_posts),
        "popular_sample": _first_sample(popular),
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
        "Fetching frontpage, r/all, and r/popular with distinct options.",
        details=(
            f"frontpage: {FRONTPAGE_CATEGORY}, limit={FRONTPAGE_LIMIT}",
            f"all: {ALL_CATEGORY}, time={ALL_TIME_FILTER}, limit={ALL_LIMIT}",
            f"popular: {POPULAR_CATEGORY}, limit={POPULAR_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    frontpage_sample = evidence["frontpage_sample"]
    all_sample = evidence["all_sample"]
    popular_sample = evidence["popular_sample"]
    console.demo_step(
        "Observed Feed Buckets",
        "Each feed returned its own count and first-post sample.",
        details=(
            f"frontpage count: {evidence['frontpage_count']}; "
            f"first subreddit: {frontpage_sample.get('subreddit')}",
            f"r/all count: {evidence['all_count']}; "
            f"first subreddit: {all_sample.get('subreddit')}",
            f"r/popular count: {evidence['popular_count']}; "
            f"first subreddit: {popular_sample.get('subreddit')}",
            f"frontpage first title: {frontpage_sample.get('title')}",
        ),
    )
    console.print(evidence)
    counts = (
        evidence["frontpage_count"],
        evidence["all_count"],
        evidence["popular_count"],
    )
    if min(counts) <= 0:
        msg = "Expected every global feed bucket to return at least one post."
        raise RuntimeError(msg)
    console.demo_outcome("The live feed families are reachable and distinct.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "all_count": 5,
  "frontpage_count": 5,
  "popular_count": 5,
  "frontpage_sample": {"permalink": "/r/...", "subreddit": "...", "title": "..."}
}
""".strip()
