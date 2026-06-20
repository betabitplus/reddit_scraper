# %%
"""Reddit search scenario: global query results.

Why:
    Verifies that the public scraper can search Reddit globally and return
    normalized listing items.

Covers:
    Area: search
    Behavior: global query search
    Interface: `reddit_scraper.RedditScraper.search_reddit`

Checks:
    If the replayed global search runs, then the serialized result shape
    matches the committed snapshot.
    If results are present, then each sampled item keeps title, subreddit, and
    permalink evidence.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.search.test_search_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/search/test_search_pipeline.py
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
SEARCH_QUERY = "Avengers: Doomsday"
SEARCH_LIMIT = 5


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
        "query": SEARCH_QUERY,
        "limit": SEARCH_LIMIT,
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(query: str, limit: int, proxy: str | None, timeout: int) -> list[dict]:
    """Run global Reddit search."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        return scraper.search_reddit(
            query,
            options=reddit_scraper.SearchOptions(limit=limit),
        )


def serialize_response(results: list[dict]) -> dict:
    """Serialize search results for snapshot comparison."""
    subreddits = sorted({r.get("subreddit") for r in results if r.get("subreddit")})
    titles = [r.get("title", "") for r in results][:3]
    return {
        "count": len(results),
        "sample_titles": titles,
        "subreddits": subreddits[:5],
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


def test_search_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_search_pipeline_hermetic"
    )
    inputs = load_inputs()
    results = run_pipeline(**inputs)
    actual = serialize_response(results)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live Reddit global search demo."""
    console.rule("[header]TEST: Reddit Global Search[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    result_summary = serialize_response(response)
    samples = (response or [])[:2]

    console.rule("[subheader]Scenario[/subheader]")
    console.print("[info]Run a global Reddit search and summarize results.[/info]")

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Query:[/key] [value]{SEARCH_QUERY}[/value]")
    console.print(f"[key]Limit:[/key] [value]{SEARCH_LIMIT}[/value]")
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Execute a global search")
    console.print("[key]2)[/key] Summarize top titles and subreddits")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        f"[key]Result count:[/key] [value]{result_summary.get('count')}[/value]"
    )
    console.print(
        "[key]Sample titles:[/key] "
        f"[value]{result_summary.get('sample_titles')}[/value]"
    )
    console.print(
        f"[key]Subreddits:[/key] [value]{result_summary.get('subreddits')}[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    for item in samples:
        console.print(f"[key]Title:[/key] [value]{item.get('title')}[/value]")
        console.print(f"[key]Subreddit:[/key] [value]{item.get('subreddit')}[/value]")
        console.print(
            "[key]Permalink:[/key] "
            f"[value]{item.get('permalink') or item.get('link')}[/value]"
        )


if __name__ == "__main__":
    main()

# %%
