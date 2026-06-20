# %%
"""Workbench scenario: popular feed geo filters.

Why:
    Proves that r/popular accepts geo filter inputs and still returns
    normalized listing evidence.

Covers:
    Area: feeds
    Behavior: geo-filtered popular listings
    Interface: live `r/popular/hot.json` requests with `geo_filter`

Checks:
    If multiple geo filters return posts, then each region count is positive.
    If region results differ, then overlap and unique subreddit evidence are
    visible.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.feeds.geo_filters
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.feeds.geo_filters
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

POPULAR_LIMIT = 5
POPULAR_CATEGORY = "hot"
GEO_FILTERS = ("us", "au", "ru")


# =============================================================================
# Helpers
# =============================================================================


def _subreddits(posts: list[dict[str, Any]]) -> set[str]:
    """Return subreddit names from one region listing."""
    return {str(post.get("subreddit")) for post in posts if post.get("subreddit")}


def _first_sample(posts: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact first-post evidence for one region listing."""
    first = posts[0] if posts else {}
    return {
        "title": first.get("title"),
        "subreddit": first.get("subreddit"),
        "permalink": first.get("permalink") or first.get("link"),
    }


def _fetch_geo_posts(
    region: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch the r/popular listing for one geo-filter bucket."""
    payload = fetch_json(
        _popular_url(POPULAR_CATEGORY),
        params={
            "geo_filter": region.lower(),
            "limit": POPULAR_LIMIT,
            "raw_json": 1,
            "t": "all",
        },
        timeout=timeout,
        proxy=proxy,
    )
    return _posts_from_listing(payload)


def _popular_url(category: str) -> str:
    """Build the r/popular URL for the configured category."""
    if category == "hot":
        return f"{REDDIT_BASE_URL}/r/popular/hot.json"
    return f"{REDDIT_BASE_URL}/r/popular/{category}.json"


def _posts_from_listing(payload: object) -> list[dict[str, Any]]:
    """Normalize post children returned by this geo-filter scenario."""
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
    """Run the isolated geo-filter comparison."""
    buckets = {region: _fetch_geo_posts(region, proxy=proxy) for region in GEO_FILTERS}
    subreddit_sets = {region: _subreddits(posts) for region, posts in buckets.items()}
    us_subs = subreddit_sets["us"]
    au_subs = subreddit_sets["au"]
    ru_subs = subreddit_sets["ru"]
    return {
        "counts": {region: len(posts) for region, posts in buckets.items()},
        "samples": {region: _first_sample(posts) for region, posts in buckets.items()},
        "overlap_us_au": sorted(us_subs & au_subs)[:5],
        "overlap_us_ru": sorted(us_subs & ru_subs)[:5],
        "overlap_au_ru": sorted(au_subs & ru_subs)[:5],
        "unique_us": sorted(us_subs - au_subs - ru_subs)[:5],
        "unique_au": sorted(au_subs - us_subs - ru_subs)[:5],
        "unique_ru": sorted(ru_subs - us_subs - au_subs)[:5],
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
        "Fetching r/popular hot posts for three geo filters.",
        details=(
            f"geo filters: {', '.join(GEO_FILTERS)}",
            f"limit: {POPULAR_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    counts = evidence["counts"]
    samples = evidence["samples"]
    console.demo_step(
        "Observed Regional Evidence",
        "Counts, overlaps, and unique subreddit names show the region buckets.",
        details=(
            f"counts: {counts}",
            f"US first subreddit: {samples['us'].get('subreddit')}",
            f"AU first subreddit: {samples['au'].get('subreddit')}",
            f"RU first subreddit: {samples['ru'].get('subreddit')}",
            f"US/AU overlap sample: {evidence['overlap_us_au']}",
            f"US-only subreddit sample: {evidence['unique_us']}",
        ),
    )
    console.print(evidence)
    if min(evidence["counts"].values()) <= 0:
        msg = "Expected every geo-filtered popular feed to return posts."
        raise RuntimeError(msg)
    console.demo_outcome("Geo-filtered popular listings returned inspectable data.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "counts": {"au": 5, "ru": 5, "us": 5},
  "overlap_us_au": ["..."],
  "unique_us": ["..."]
}
""".strip()
