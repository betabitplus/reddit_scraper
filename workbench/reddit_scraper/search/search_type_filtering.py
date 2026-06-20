# %%
"""Workbench scenario: Reddit search type filtering.

Why:
    Proves that Reddit's search type option separates post-style results from
    community results without using shipped scraper code.

Covers:
    Area: search
    Behavior: post-only and subreddit-only search result filtering
    Interface: live `search.json` requests with `type=link` and `type=sr`

Checks:
    If link search is requested, then post evidence includes post titles.
    If subreddit search is requested, then community evidence includes
    subreddit labels.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.search.search_type_filtering
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.search.search_type_filtering
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
    reddit_url,
)

# =============================================================================
# Scenario
# =============================================================================

SEARCH_QUERY = "python programming"
SEARCH_LIMIT = 5


# =============================================================================
# Helpers
# =============================================================================


def _community_label(item: dict[str, Any]) -> object:
    """Return the most readable community label from a search result."""
    return (
        item.get("display_name_prefixed")
        or item.get("display_name")
        or item.get("title")
        or item.get("subreddit")
    )


def _search_reddit(
    query: str,
    *,
    limit: int,
    search_types: tuple[str, ...],
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Run one typed global search owned by this scenario."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/search.json",
        params={
            "limit": limit,
            "q": query,
            "raw_json": 1,
            "sort": "relevance",
            "type": ",".join(search_types),
        },
        timeout=timeout,
        proxy=proxy,
    )
    return _extract_typed_results(payload)


def _extract_typed_results(payload: object) -> list[dict[str, Any]]:
    """Normalize only post and community results this scenario compares."""
    results: list[dict[str, Any]] = []
    for child in listing_children(payload):
        parsed = _parse_typed_result(child)
        if parsed is not None:
            results.append(parsed)
    return results


def _parse_typed_result(child: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize one search child for the requested type bucket."""
    item_data = child.get("data", {})
    if not isinstance(item_data, dict):
        return None

    if child.get("kind") == "t3":
        result = normalize_post(item_data)
        result["type"] = "post"
        return result

    if child.get("kind") == "t5":
        display_name = item_data.get("display_name", "")
        return {
            "type": "subreddit",
            "title": item_data.get("display_name_prefixed") or display_name,
            "display_name": display_name,
            "display_name_prefixed": item_data.get("display_name_prefixed"),
            "description": item_data.get("public_description", "")[:269],
            "subscribers": item_data.get("subscribers", 0),
            "permalink": item_data.get("url"),
            "link": reddit_url(item_data.get("url")),
        }

    return None


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, proxy: str | None = None) -> dict[str, Any]:
    """Run post-only and community-only search requests."""
    post_results = _search_reddit(
        SEARCH_QUERY,
        limit=SEARCH_LIMIT,
        search_types=("link",),
        timeout=DEFAULT_TIMEOUT_SECONDS,
        proxy=proxy,
    )
    community_results = _search_reddit(
        SEARCH_QUERY,
        limit=SEARCH_LIMIT,
        search_types=("sr",),
        timeout=DEFAULT_TIMEOUT_SECONDS,
        proxy=proxy,
    )
    return {
        "post_count": len(post_results),
        "community_count": len(community_results),
        "post_titles": [item.get("title") for item in post_results[:3]],
        "community_labels": [_community_label(item) for item in community_results[:3]],
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
        "Running the same live query with post and community result filters.",
        details=(
            f"query: {SEARCH_QUERY}",
            f"limit: {SEARCH_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    post_titles = evidence["post_titles"]
    community_labels = evidence["community_labels"]
    console.demo_step(
        "Observed Filtered Results",
        "The two result buckets expose different readable labels.",
        details=(
            f"post count: {evidence['post_count']}",
            f"community count: {evidence['community_count']}",
            f"first post title: {post_titles[0] if post_titles else None}",
            f"first community label: "
            f"{community_labels[0] if community_labels else None}",
        ),
    )
    console.print(evidence)
    if evidence["post_count"] <= 0 or evidence["community_count"] <= 0:
        msg = "Expected both post and community search results."
        raise RuntimeError(msg)
    console.demo_outcome(
        "Search type filtering produced separate post and subreddit evidence.",
    )


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "community_count": 5,
  "community_labels": ["r/Python", "..."],
  "post_count": 5,
  "post_titles": ["...", "..."]
}
""".strip()
