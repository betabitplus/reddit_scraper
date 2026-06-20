# %%
"""Reddit subreddit-posts scenario: scoped search and listings.

Why:
    Verifies that subreddit-scoped search and subreddit post listing work
    through the public scraper options.

Covers:
    Area: subreddit posts
    Behavior: subreddit search and hot post listing
    Interface: `search_subreddit` and `fetch_subreddit_posts`

Checks:
    If subreddit searches replay successfully, then per-subreddit result counts
    match the committed snapshot.
    If hot posts are fetched for the target subreddit, then count and permalink
    evidence match the committed snapshot.

Examples:
    Run manually:
        uv run python -m \
            tests.reddit_scraper.e2e.subreddit_posts.test_subreddit_posts_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/subreddit_posts/test_subreddit_posts_pipeline.py
"""

from __future__ import annotations

import os

import pytest
from py_lib_tooling import (
    console,
    require_vcr_cassette_or_record_mode,
)
from syrupy.assertion import SnapshotAssertion

import reddit_scraper

pytestmark = [
    pytest.mark.hermetic,
    pytest.mark.vcr,
]

# =============================================================================
# Scenario
# =============================================================================
CLIENT_TIMEOUT = 15
TARGET_SUBREDDITS = ["marvelstudios", "Marvel"]
SUBREDDIT_SEARCH_QUERY = "Avengers Doomsday"
SUBREDDIT_SEARCH_LIMIT = 3
SUBREDDIT_SEARCH_SORT = "relevance"

HOT_POSTS_SUBREDDIT = "marvelstudios"
HOT_POSTS_LIMIT = 3
HOT_POSTS_CATEGORY = "hot"


# =============================================================================
# Helpers
# =============================================================================


def get_proxy() -> str | None:
    """Get proxy from environment variable (demo-only)."""
    return os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


# =============================================================================
# Pipeline
# =============================================================================


def load_inputs() -> dict:
    """Load inputs for the pipeline."""
    return {
        "target_subreddits": TARGET_SUBREDDITS,
        "search_query": SUBREDDIT_SEARCH_QUERY,
        "search_limit": SUBREDDIT_SEARCH_LIMIT,
        "search_sort": SUBREDDIT_SEARCH_SORT,
        "hot_subreddit": HOT_POSTS_SUBREDDIT,
        "hot_limit": HOT_POSTS_LIMIT,
        "hot_category": HOT_POSTS_CATEGORY,
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(
    target_subreddits: list[str],
    search_query: str,
    search_limit: int,
    search_sort: str,
    hot_subreddit: str,
    hot_limit: int,
    hot_category: str,
    proxy: str | None,
    timeout: int,
) -> dict:
    """Run subreddit search + hot posts pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        search_results: dict[str, list[dict]] = {}
        for subreddit in target_subreddits:
            search_results[subreddit] = scraper.search_subreddit(
                subreddit,
                search_query,
                options=reddit_scraper.SubredditSearchOptions(
                    limit=search_limit,
                    sort=search_sort,
                ),
            )

        hot_posts = scraper.fetch_subreddit_posts(
            hot_subreddit,
            options=reddit_scraper.SubredditPostsOptions(
                limit=hot_limit,
                category=hot_category,
            ),
        )

    return {
        "search_results": search_results,
        "hot_posts": hot_posts,
    }


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    search_results = response["search_results"]
    hot_posts = response["hot_posts"]
    return {
        "search_counts": {key: len(value) for key, value in search_results.items()},
        "hot_posts_count": len(hot_posts),
        "hot_permalinks": [p.get("permalink") for p in hot_posts[:2]],
    }


# =============================================================================
# Assertions
# =============================================================================


def assert_pipeline_response(actual: object, snapshot: SnapshotAssertion) -> None:
    """Verify the serialized response matches the committed scenario snapshot."""
    assert actual == snapshot


# =============================================================================
# Tests
# =============================================================================


def test_subreddit_posts_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_subreddit_posts_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live subreddit search and post listing demo."""
    console.rule("[header]TEST: Subreddit Posts[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    search_results = response.get("search_results") or {}
    hot_posts = response.get("hot_posts") or []
    first_sub = TARGET_SUBREDDITS[0] if TARGET_SUBREDDITS else ""
    result_summary = serialize_response(response)
    search_samples = (search_results.get(first_sub) or [])[:2]
    hot_samples = hot_posts[:2]

    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Search within target subreddits and fetch hot posts "
        "for a specific subreddit.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Target subreddits:[/key] [value]{TARGET_SUBREDDITS}[/value]")
    console.print(
        "[key]Search:[/key] "
        f"[value]query='{SUBREDDIT_SEARCH_QUERY}', "
        f"limit={SUBREDDIT_SEARCH_LIMIT}, sort={SUBREDDIT_SEARCH_SORT}[/value]"
    )
    console.print(
        "[key]Hot posts:[/key] "
        f"[value]r/{HOT_POSTS_SUBREDDIT}, limit={HOT_POSTS_LIMIT}, "
        f"category={HOT_POSTS_CATEGORY}[/value]"
    )
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Search within each target subreddit")
    console.print("[key]2)[/key] Fetch hot posts for the configured subreddit")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        "[key]Search counts:[/key] "
        f"[value]{result_summary.get('search_counts')}[/value]"
    )
    console.print(
        "[key]Hot posts count:[/key] "
        f"[value]{result_summary.get('hot_posts_count')}[/value]"
    )
    console.print(
        "[key]Hot permalinks:[/key] "
        f"[value]{result_summary.get('hot_permalinks')}[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    console.print("[info]Search samples:[/info]")
    for item in search_samples:
        console.print(f"[key]Title:[/key] [value]{item.get('title')}[/value]")
        console.print(f"[key]Subreddit:[/key] [value]{item.get('subreddit')}[/value]")
        console.print(
            "[key]Permalink:[/key] "
            f"[value]{item.get('permalink') or item.get('link')}[/value]"
        )
    console.print("[info]Hot samples:[/info]")
    for item in hot_samples:
        console.print(f"[key]Title:[/key] [value]{item.get('title')}[/value]")
        console.print(f"[key]Subreddit:[/key] [value]{item.get('subreddit')}[/value]")
        console.print(
            "[key]Permalink:[/key] "
            f"[value]{item.get('permalink') or item.get('link')}[/value]"
        )


if __name__ == "__main__":
    main()

# %%
