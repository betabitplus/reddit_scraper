# %%
"""Reddit feeds scenario: global listing families.

Why:
    Verifies that the public scraper returns normalized listings for the
    frontpage, r/all, and r/popular feed families.

Covers:
    Area: feeds
    Behavior: global feed listing retrieval
    Interface: `fetch_frontpage`, `fetch_all`, and `fetch_popular`

Checks:
    If global feed requests replay successfully, then each feed count and
    sample subreddit shape matches the committed snapshot.
    If distinct feed options are used, then each serialized feed bucket remains
    separate.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.feeds.test_global_feeds_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/feeds/test_global_feeds_pipeline.py
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


def get_proxy() -> str | None:
    """Get proxy from environment variable (demo-only)."""
    return os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


# =============================================================================
# Pipeline
# =============================================================================


def load_inputs() -> dict:
    """Load inputs for the pipeline."""
    return {
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(proxy: str | None, timeout: int) -> dict:
    """Run global feeds pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        frontpage = scraper.fetch_frontpage(
            options=reddit_scraper.FeedOptions(
                limit=FRONTPAGE_LIMIT,
                category=FRONTPAGE_CATEGORY,
            )
        )
        all_posts = scraper.fetch_all(
            options=reddit_scraper.FeedOptions(
                limit=ALL_LIMIT,
                category=ALL_CATEGORY,
                time_filter=ALL_TIME_FILTER,
            )
        )
        popular = scraper.fetch_popular(
            options=reddit_scraper.PopularFeedOptions(
                limit=POPULAR_LIMIT,
                category=POPULAR_CATEGORY,
            )
        )

    return {
        "frontpage": frontpage,
        "all_posts": all_posts,
        "popular": popular,
    }


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    return {
        "frontpage_count": len(response.get("frontpage") or []),
        "all_count": len(response.get("all_posts") or []),
        "popular_count": len(response.get("popular") or []),
        "frontpage_subreddits": [
            p.get("subreddit") for p in (response.get("frontpage") or [])[:3]
        ],
        "popular_subreddits": [
            p.get("subreddit") for p in (response.get("popular") or [])[:3]
        ],
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


def test_global_feeds_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_global_feeds_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live global feeds demo."""
    console.rule("[header]TEST: Global Feeds[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    frontpage = response.get("frontpage") or []
    all_posts = response.get("all_posts") or []
    popular = response.get("popular") or []
    result_summary = serialize_response(response)
    frontpage_sample = frontpage[0] if frontpage else {}
    all_sample = all_posts[0] if all_posts else {}
    popular_sample = popular[0] if popular else {}

    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Validate frontpage, r/all, and r/popular feeds "
        "with distinct parameters.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(
        "[key]Frontpage:[/key] "
        f"[value]limit={FRONTPAGE_LIMIT}, "
        f"category={FRONTPAGE_CATEGORY}[/value]"
    )
    console.print(
        "[key]All:[/key] "
        f"[value]limit={ALL_LIMIT}, category={ALL_CATEGORY}, "
        f"time={ALL_TIME_FILTER}[/value]"
    )
    console.print(
        "[key]Popular:[/key] "
        f"[value]limit={POPULAR_LIMIT}, "
        f"category={POPULAR_CATEGORY}[/value]"
    )
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Fetch frontpage feed")
    console.print("[key]2)[/key] Fetch r/all feed")
    console.print("[key]3)[/key] Fetch r/popular feed")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        "[key]Counts:[/key] "
        f"frontpage={result_summary.get('frontpage_count')}, "
        f"all={result_summary.get('all_count')}, "
        f"popular={result_summary.get('popular_count')}"
    )
    console.print(
        "[key]Frontpage subreddits:[/key] "
        f"[value]{result_summary.get('frontpage_subreddits')}[/value]"
    )
    console.print(
        "[key]Popular subreddits:[/key] "
        f"[value]{result_summary.get('popular_subreddits')}[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    console.print("[info]Frontpage sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{frontpage_sample.get('title')}[/value]")
    console.print(
        f"[key]Subreddit:[/key] [value]{frontpage_sample.get('subreddit')}[/value]"
    )
    frontpage_link = frontpage_sample.get("permalink") or frontpage_sample.get("link")
    console.print(f"[key]Permalink:[/key] [value]{frontpage_link}[/value]")
    console.print("[info]All sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{all_sample.get('title')}[/value]")
    console.print(f"[key]Subreddit:[/key] [value]{all_sample.get('subreddit')}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{all_sample.get('permalink') or all_sample.get('link')}[/value]"
    )
    console.print("[info]Popular sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{popular_sample.get('title')}[/value]")
    console.print(
        f"[key]Subreddit:[/key] [value]{popular_sample.get('subreddit')}[/value]"
    )
    popular_link = popular_sample.get("permalink") or popular_sample.get("link")
    console.print(f"[key]Permalink:[/key] [value]{popular_link}[/value]")


if __name__ == "__main__":
    main()

# %%
