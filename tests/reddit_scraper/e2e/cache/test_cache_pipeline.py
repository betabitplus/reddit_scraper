# %%
"""Reddit cache scenario: repeated search reuse.

Why:
    Verifies that a public scraper instance can cache one search response and
    reuse it for the same request shape.

Covers:
    Area: cache
    Behavior: API response cache reuse
    Interface: `reddit_scraper.RedditScraper` with `ScraperConfig.cache_dir`

Checks:
    If the cache is cleared before the first search, then the first search
    populates cache evidence in the serialized result.
    If the same search runs again, then the cache entry count stays stable and
    the repeated result shape matches the committed snapshot.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.cache.test_cache_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/cache/test_cache_pipeline.py
"""

from __future__ import annotations

import os
from pathlib import Path

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
SEARCH_LIMIT = 3
CACHE_DIR = Path(__file__).parent / ".cache"


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
        "cache_dir": str(CACHE_DIR),
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(
    query: str,
    limit: int,
    cache_dir: str,
    proxy: str | None,
    timeout: int,
) -> dict:
    """Run cache behavior pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(
            proxy=proxy,
            timeout=timeout,
            cache_dir=cache_dir,
        )
    ) as scraper:
        scraper.clear_cache()
        stats_before = scraper.cache_stats()
        first_results = scraper.search_reddit(
            query,
            options=reddit_scraper.SearchOptions(limit=limit),
        )
        stats_after_first = scraper.cache_stats()
        second_results = scraper.search_reddit(
            query,
            options=reddit_scraper.SearchOptions(limit=limit),
        )
        stats_after_second = scraper.cache_stats()

    return {
        "first_count": len(first_results or []),
        "second_count": len(second_results or []),
        "sample": (first_results or [None])[0],
        "stats_before": stats_before,
        "stats_after_first": stats_after_first,
        "stats_after_second": stats_after_second,
    }


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    return {
        "first_count": response.get("first_count"),
        "second_count": response.get("second_count"),
        "entries_before": response.get("stats_before", {}).get("entry_count"),
        "entries_after_first": response.get("stats_after_first", {}).get("entry_count"),
        "entries_after_second": response.get("stats_after_second", {}).get(
            "entry_count"
        ),
        "cache_enabled": response.get("stats_after_first", {}).get("enabled"),
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


def test_cache_pipeline_hermetic(
    snapshot: SnapshotAssertion,
    tmp_path: Path,
) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_cache_pipeline_hermetic"
    )
    """Hermetic pipeline test for cache behavior."""
    inputs = load_inputs()
    inputs["cache_dir"] = str(tmp_path / "cache")
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live Reddit cache behavior demo."""
    console.rule("[header]TEST: Cache Behavior[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    entries_before = response.get("stats_before", {}).get("entry_count") or 0
    entries_after_first = response.get("stats_after_first", {}).get("entry_count") or 0
    entries_after_second = (
        response.get("stats_after_second", {}).get("entry_count") or 0
    )
    sample = response.get("sample") or {}
    cache_enabled = response.get("stats_after_first", {}).get("enabled")
    cache_populated = entries_after_first > entries_before and entries_after_first > 0
    cache_reused = entries_after_second == entries_after_first
    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Validate that global search results are cached "
        "and reused on a repeat call.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Query:[/key] [value]{inputs['query']}[/value]")
    console.print(f"[key]Limit:[/key] [value]{inputs['limit']}[/value]")
    console.print(f"[key]Cache dir:[/key] [value]{inputs['cache_dir']}[/value]")
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Clear cache, then run the first search")
    console.print("[key]2)[/key] Run the same search again to hit cache")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        "[value]Cache is "
        f"{'enabled' if cache_enabled else 'disabled'} for this run.[/value]"
    )
    console.print(
        "[value]Cache cleared first: "
        f"{'yes' if entries_before == 0 else 'no'} "
        f"(entries before search: {entries_before}).[/value]"
    )
    console.print(
        "[value]First search: "
        f"{response.get('first_count')} items; "
        f"cache entries after first search: {entries_after_first}.[/value]"
    )
    console.print(
        "[value]Second search: "
        f"{response.get('second_count')} items; "
        f"cache entries after second search: {entries_after_second}.[/value]"
    )
    console.print(
        "[value]Cache populated: "
        f"{'yes' if cache_populated else 'no'}; "
        "cache reused: "
        f"{'yes' if cache_reused else 'no'}.[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    console.print(
        "[info]Sample item from the first run "
        "(should remain available on repeat):[/info]"
    )
    console.print(f"[key]Title:[/key] [value]{sample.get('title')}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{sample.get('permalink') or sample.get('link')}[/value]"
    )
    console.print(f"[key]Subreddit:[/key] [value]{sample.get('subreddit')}[/value]")


if __name__ == "__main__":
    main()

# %%
