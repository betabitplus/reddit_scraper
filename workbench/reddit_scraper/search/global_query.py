# %%
"""Workbench scenario: global Reddit search.

Why:
    Proves the core global search flow with direct Reddit JSON requests,
    independent from the shipped scraper runtime.

Covers:
    Area: search
    Behavior: global query search and normalized result evidence
    Interface: live `https://www.reddit.com/search.json` request

Checks:
    If the global query returns results, then the evidence includes a positive
    result count.
    If sampled post results are present, then each sample keeps title,
    subreddit, and permalink evidence.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.search.global_query
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.search.global_query
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

SEARCH_QUERY = "Avengers: Doomsday"
SEARCH_LIMIT = 5


# =============================================================================
# Helpers
# =============================================================================


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize global search evidence for console output."""
    return {
        "count": len(results),
        "sample_titles": [item.get("title") for item in results[:3]],
        "subreddits": sorted(
            {item.get("subreddit") for item in results if item.get("subreddit")}
        )[:5],
        "samples": _summarize_posts(results[:2]),
    }


def _search_reddit(
    query: str,
    *,
    limit: int,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Run the one global post search this scenario owns."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/search.json",
        params={
            "limit": limit,
            "q": query,
            "raw_json": 1,
            "sort": "relevance",
            "type": "link",
        },
        timeout=timeout,
        proxy=proxy,
    )
    return _extract_post_results(payload)


def _extract_post_results(payload: object) -> list[dict[str, Any]]:
    """Normalize post search children for this scenario."""
    results: list[dict[str, Any]] = []
    for child in listing_children(payload):
        if child.get("kind") != "t3":
            continue
        data = child.get("data", {})
        if isinstance(data, dict):
            result = normalize_post(data)
            result["type"] = "post"
            result["description"] = data.get("selftext", "")[:269]
            results.append(result)
    return results


def _summarize_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return compact post evidence for this search scenario."""
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
    """Run the isolated global search behavior."""
    results = _search_reddit(
        SEARCH_QUERY,
        limit=SEARCH_LIMIT,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        proxy=proxy,
    )
    return _summarize(results)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the workbench script as a narrative manual demo."""
    console.demo_intro(__doc__)
    proxy = get_proxy()
    console.demo_step(
        "Scenario",
        "Running one live global search through Reddit JSON.",
        details=(
            f"query: {SEARCH_QUERY}",
            f"limit: {SEARCH_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    samples = evidence["samples"]
    first_sample = samples[0] if samples else {}
    console.demo_step(
        "Observed Search Results",
        "The response was normalized into count, subreddit, and sample evidence.",
        details=(
            f"result count: {evidence['count']}",
            f"subreddits seen: {', '.join(evidence['subreddits'])}",
            f"first title: {first_sample.get('title')}",
            f"first permalink: {first_sample.get('permalink')}",
        ),
    )
    console.print(evidence)
    if evidence["count"] <= 0:
        msg = "Expected at least one global search result."
        raise RuntimeError(msg)
    console.demo_outcome(
        "The live search flow produced inspectable Reddit result evidence.",
    )


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "count": 5,
  "sample_titles": ["...", "..."],
  "samples": [{"permalink": "/r/...", "subreddit": "...", "title": "..."}],
  "subreddits": ["..."]
}
""".strip()
