# %%
"""Reddit feeds scenario: pagination and time filters.

Why:
    Verifies that subreddit feed and search flows preserve time-filter and
    pagination behavior through public options.

Covers:
    Area: feeds
    Behavior: time-filtered posts and after-cursor pagination
    Interface: `fetch_subreddit_posts` and `search_subreddit`

Checks:
    If time-filtered top posts replay successfully, then the serialized count
    matches the committed snapshot.
    If an after cursor is available, then the second page is serialized without
    hiding duplicate-title evidence.

Examples:
    Run manually:
        uv run python -m \
            tests.reddit_scraper.e2e.feeds.test_pagination_timefilter_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/feeds/test_pagination_timefilter_pipeline.py
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

TOP_POSTS_SUBREDDIT = "marvelstudios"
TOP_POSTS_LIMIT = 3
TOP_POSTS_CATEGORY = "top"
TOP_POSTS_TIME_FILTER = "week"

PAGINATION_SUBREDDIT = "marvelstudios"
PAGINATION_QUERY = "Avengers"
PAGINATION_LIMIT = 3
PAGINATION_SORT = "new"


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
    """Run pagination and time filter pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        top_posts = scraper.fetch_subreddit_posts(
            TOP_POSTS_SUBREDDIT,
            options=reddit_scraper.SubredditPostsOptions(
                limit=TOP_POSTS_LIMIT,
                category=TOP_POSTS_CATEGORY,
                time_filter=TOP_POSTS_TIME_FILTER,
            ),
        )

        page1 = scraper.search_subreddit(
            PAGINATION_SUBREDDIT,
            PAGINATION_QUERY,
            options=reddit_scraper.SubredditSearchOptions(
                limit=PAGINATION_LIMIT,
                sort=PAGINATION_SORT,
            ),
        )

        page2 = []
        if page1:
            last_link = page1[-1].get("link", "")
            if "/comments/" in last_link:
                post_id = last_link.split("/comments/")[1].split("/")[0]
                after_cursor = f"t3_{post_id}"
                page2 = scraper.search_subreddit(
                    PAGINATION_SUBREDDIT,
                    PAGINATION_QUERY,
                    options=reddit_scraper.SubredditSearchOptions(
                        limit=PAGINATION_LIMIT,
                        sort=PAGINATION_SORT,
                        after=after_cursor,
                    ),
                )

    return {"top_posts": top_posts, "page1": page1, "page2": page2}


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    page1 = response.get("page1") or []
    page2 = response.get("page2") or []
    duplicates = {r.get("title") for r in page1} & {r.get("title") for r in page2}
    return {
        "top_posts_count": len(response.get("top_posts") or []),
        "page1_count": len(page1),
        "page2_count": len(page2),
        "duplicate_titles_count": len(duplicates),
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


def test_pagination_timefilter_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_pagination_timefilter_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live pagination and time-filter demo."""
    console.rule("[header]TEST: Pagination & Time Filter[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    top_posts = response.get("top_posts") or []
    page1 = response.get("page1") or []
    page2 = response.get("page2") or []
    result_summary = serialize_response(response)
    top_sample = top_posts[0] if top_posts else {}
    page1_sample = page1[0] if page1 else {}
    page2_sample = page2[0] if page2 else {}

    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Validate time-filtered top posts and paginated search results.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(
        "[key]Top posts:[/key] "
        f"[value]r/{TOP_POSTS_SUBREDDIT}, {TOP_POSTS_CATEGORY}, "
        f"time={TOP_POSTS_TIME_FILTER}, limit={TOP_POSTS_LIMIT}[/value]"
    )
    console.print(
        "[key]Pagination:[/key] "
        f"[value]r/{PAGINATION_SUBREDDIT}, query='{PAGINATION_QUERY}', "
        f"sort={PAGINATION_SORT}, limit={PAGINATION_LIMIT}[/value]"
    )
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Fetch top posts with a time filter")
    console.print("[key]2)[/key] Fetch search page 1")
    console.print("[key]3)[/key] Fetch search page 2 using an after cursor")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        "[key]Counts:[/key] "
        f"top={result_summary.get('top_posts_count')}, "
        f"page1={result_summary.get('page1_count')}, "
        f"page2={result_summary.get('page2_count')}"
    )
    console.print(
        "[key]Duplicate titles:[/key] "
        f"[value]{result_summary.get('duplicate_titles_count')}[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    console.print("[info]Top post sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{top_sample.get('title')}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{top_sample.get('permalink') or top_sample.get('link')}[/value]"
    )
    console.print("[info]Page 1 sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{page1_sample.get('title')}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{page1_sample.get('permalink') or page1_sample.get('link')}[/value]"
    )
    console.print("[info]Page 2 sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{page2_sample.get('title')}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{page2_sample.get('permalink') or page2_sample.get('link')}[/value]"
    )


if __name__ == "__main__":
    main()

# %%
