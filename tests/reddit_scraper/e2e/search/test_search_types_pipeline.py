# %%
"""Reddit search scenario: result type filtering.

Why:
    Verifies that the public search API keeps post and subreddit result
    filters distinct.

Covers:
    Area: search
    Behavior: search-type filtering
    Interface: `reddit_scraper.RedditScraper.search_reddit`

Checks:
    If link search is requested, then the serialized response matches the
    committed post-result snapshot fields.
    If subreddit search is requested, then the serialized response matches the
    committed subreddit-result snapshot fields.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.search.test_search_types_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/search/test_search_types_pipeline.py
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
SEARCH_QUERY = "python programming"
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
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(proxy: str | None, timeout: int) -> dict:
    """Run search type filtering pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        post_results = scraper.search_reddit(
            SEARCH_QUERY,
            options=reddit_scraper.SearchOptions(
                limit=SEARCH_LIMIT,
                search_types=["link"],
            ),
        )
        sr_results = scraper.search_reddit(
            SEARCH_QUERY,
            options=reddit_scraper.SearchOptions(
                limit=SEARCH_LIMIT,
                search_types=["sr"],
            ),
        )

    return {
        "post_results": post_results,
        "sr_results": sr_results,
    }


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    sr_titles = []
    for item in response.get("sr_results") or []:
        label = (
            item.get("display_name_prefixed")
            or item.get("display_name")
            or item.get("name")
            or item.get("subreddit")
            or item.get("title")
        )
        sr_titles.append(label)
    return {
        "post_count": len(response.get("post_results") or []),
        "sr_count": len(response.get("sr_results") or []),
        "post_titles": [
            r.get("title") for r in (response.get("post_results") or [])[:3]
        ],
        "sr_titles": sr_titles[:3],
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


def test_search_types_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_search_types_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live Reddit search type filtering demo."""
    console.rule("[header]TEST: Search Type Filtering[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    result_summary = serialize_response(response)
    post_samples = (response.get("post_results") or [])[:2]
    sr_samples = (response.get("sr_results") or [])[:2]

    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Compare post-only search results vs subreddit-only results.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Query:[/key] [value]{SEARCH_QUERY}[/value]")
    console.print(f"[key]Limit:[/key] [value]{SEARCH_LIMIT}[/value]")
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Search with type=link (posts)")
    console.print("[key]2)[/key] Search with type=sr (subreddits)")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        f"[key]Post count:[/key] [value]{result_summary.get('post_count')}[/value]"
    )
    console.print(
        f"[key]Subreddit count:[/key] [value]{result_summary.get('sr_count')}[/value]"
    )
    console.print(
        f"[key]Post titles:[/key] [value]{result_summary.get('post_titles')}[/value]"
    )
    console.print(
        f"[key]Community names:[/key] [value]{result_summary.get('sr_titles')}[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    console.print("[info]Post samples:[/info]")
    for item in post_samples:
        console.print(f"[key]Title:[/key] [value]{item.get('title')}[/value]")
        console.print(f"[key]Subreddit:[/key] [value]{item.get('subreddit')}[/value]")
        console.print(
            "[key]Permalink:[/key] "
            f"[value]{item.get('permalink') or item.get('link')}[/value]"
        )
    console.print("[info]Community samples:[/info]")
    for item in sr_samples:
        label = (
            item.get("display_name_prefixed")
            or item.get("display_name")
            or item.get("name")
            or item.get("subreddit")
            or item.get("title")
        )
        console.print(f"[key]Name:[/key] [value]{label}[/value]")
        console.print(
            "[key]Permalink:[/key] "
            f"[value]{item.get('permalink') or item.get('link')}[/value]"
        )


if __name__ == "__main__":
    main()

# %%
