# %%
"""Reddit retry scenario: recoverable public request flow.

Why:
    Verifies that public request flows complete for normal queries and degrade
    predictably for an invalid subreddit under replay.

Covers:
    Area: retry
    Behavior: successful repeated requests and invalid subreddit fallback
    Interface: `search_reddit` and `fetch_subreddit_posts`

Checks:
    If replayed searches complete, then query result counts match the committed
    snapshot.
    If the invalid subreddit request completes, then it serializes as an empty
    public result instead of raising.

Notes:
    Deterministic transport retry mechanics live in integration tests because
    they use private request seams.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.retry.test_retry_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/retry/test_retry_pipeline.py
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
        "queries": ["python", "test0", "test1"],
        "invalid_subreddit": "thisdoesnotexist12345xyz",
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(
    queries: list[str],
    invalid_subreddit: str,
    proxy: str | None,
    timeout: int,
) -> dict:
    """Run retry/backoff validation pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        results = [
            scraper.search_reddit(
                query,
                options=reddit_scraper.SearchOptions(limit=2),
            )
            for query in queries
        ]
        invalid_results = scraper.fetch_subreddit_posts(
            invalid_subreddit,
            options=reddit_scraper.SubredditPostsOptions(limit=1),
        )

    return {
        "query_results": results,
        "invalid_results": invalid_results,
    }


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    query_results = response.get("query_results") or []
    return {
        "queries": [len(r) for r in query_results],
        "invalid_empty": not response.get("invalid_results"),
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


def test_retry_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_retry_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live public retry-flow demo."""
    console.rule("[header]TEST: Retry/Backoff[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    query_results = response.get("query_results") or []
    samples = []
    for idx, query in enumerate(inputs["queries"]):
        items = query_results[idx] if idx < len(query_results) else []
        samples.append(
            {
                "query": query,
                "count": len(items or []),
                "permalink": (items[0] if items else {}).get("permalink")
                or (items[0] if items else {}).get("link"),
                "title": (items[0] if items else {}).get("title"),
            }
        )
    result_summary = serialize_response(response)

    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Run multiple queries and confirm invalid subreddit returns empty.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Queries:[/key] [value]{inputs['queries']}[/value]")
    console.print(
        f"[key]Invalid subreddit:[/key] [value]{inputs['invalid_subreddit']}[/value]"
    )
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Execute searches for each query")
    console.print("[key]2)[/key] Fetch posts for an invalid subreddit")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        "[key]Expected:[/key] "
        "[value]each valid query returns > 0 results; "
        "invalid subreddit returns 0[/value]"
    )
    all_valid_ok = all(sample.get("count", 0) > 0 for sample in samples)
    invalid_ok = result_summary.get("invalid_empty") is True
    console.print(
        "[key]Overall status:[/key] "
        f"[value]{'OK' if all_valid_ok and invalid_ok else 'CHECK'}[/value]"
    )
    console.print(
        "[key]Valid queries result counts:[/key] "
        f"[value]{result_summary.get('queries')}[/value]"
    )
    console.print(
        "[key]Invalid subreddit empty:[/key] "
        f"[value]{result_summary.get('invalid_empty')}[/value]"
    )
    console.rule("[subheader]Examples[/subheader]")
    console.print("[info]Valid queries: top result + count (must be > 0).[/info]")
    for sample in samples:
        ok_flag = sample.get("count", 0) > 0
        console.print(f"[key]Query:[/key] [value]{sample.get('query')}[/value]")
        console.print(f"[key]Results found:[/key] [value]{sample.get('count')}[/value]")
        console.print(
            f"[key]Meets expectation (>0):[/key] "
            f"[value]{'yes' if ok_flag else 'no'}[/value]"
        )
        console.print(
            f"[key]Top result title:[/key] [value]{sample.get('title')}[/value]"
        )
        console.print(
            f"[key]Top result link:[/key] [value]{sample.get('permalink')}[/value]"
        )
    console.print("[info]Invalid subreddit: should return 0 results.[/info]")
    invalid_count = len(response.get("invalid_results") or [])
    console.print(
        f"[key]Invalid subreddit:[/key] [value]{inputs['invalid_subreddit']}[/value]"
    )
    console.print(f"[key]Results found:[/key] [value]{invalid_count}[/value]")
    console.print(
        f"[key]Meets expectation (0):[/key] "
        f"[value]{'yes' if invalid_count == 0 else 'no'}[/value]"
    )


if __name__ == "__main__":
    main()

# %%
