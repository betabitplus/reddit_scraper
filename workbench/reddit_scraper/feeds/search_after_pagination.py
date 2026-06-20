# %%
"""Workbench scenario: search after-cursor pagination.

Why:
    Proves that subreddit search results can derive an `after` cursor and
    request a second page without shipped scraper code.

Covers:
    Area: feeds
    Behavior: after-cursor pagination for subreddit search
    Interface: live subreddit `search.json` requests with `after`

Checks:
    If the first search page has a Reddit post ID, then an after cursor is derived.
    If the cursor is used, then second-page and duplicate-title evidence is visible.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.feeds.search_after_pagination
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.feeds.search_after_pagination
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

SUBREDDIT = "marvelstudios"
SEARCH_QUERY = "Avengers"
SEARCH_LIMIT = 3
SEARCH_SORT = "new"


# =============================================================================
# Helpers
# =============================================================================


def _after_from_last_result(results: list[dict[str, Any]]) -> str | None:
    """Derive Reddit's `t3_` cursor from the final result permalink."""
    if not results:
        return None
    link = str(results[-1].get("link") or results[-1].get("permalink") or "")
    if "/comments/" not in link:
        return None
    post_id = link.split("/comments/", maxsplit=1)[1].split("/", maxsplit=1)[0]
    return f"t3_{post_id}" if post_id else None


def _first_title(results: list[dict[str, Any]]) -> object:
    """Return first-title evidence for readable output."""
    return (results[0] if results else {}).get("title")


def _search_subreddit(
    *,
    after: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Run one subreddit search page for this pagination scenario."""
    params: dict[str, object] = {
        "limit": SEARCH_LIMIT,
        "q": SEARCH_QUERY,
        "raw_json": 1,
        "restrict_sr": "on",
        "sort": SEARCH_SORT,
        "type": "link",
    }
    if after:
        params["after"] = after

    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{SUBREDDIT}/search.json",
        params=params,
        timeout=timeout,
        proxy=proxy,
    )
    return _extract_post_results(payload)


def _extract_post_results(payload: object) -> list[dict[str, Any]]:
    """Normalize post search results for cursor evidence."""
    results: list[dict[str, Any]] = []
    for child in listing_children(payload):
        if child.get("kind") != "t3":
            continue
        data = child.get("data", {})
        if isinstance(data, dict):
            result = normalize_post(data)
            result["type"] = "post"
            results.append(result)
    return results


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, proxy: str | None = None) -> dict[str, Any]:
    """Run a two-page subreddit search pagination probe."""
    page1 = _search_subreddit(proxy=proxy)
    after = _after_from_last_result(page1)
    page2: list[dict[str, Any]] = []
    if after:
        page2 = _search_subreddit(after=after, proxy=proxy)
    duplicates = {item.get("title") for item in page1} & {
        item.get("title") for item in page2
    }
    return {
        "page1_count": len(page1),
        "after_cursor": after,
        "after_cursor_present": after is not None,
        "page2_count": len(page2),
        "duplicate_titles_count": len(duplicates),
        "page1_first": _first_title(page1),
        "page2_first": _first_title(page2),
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
        "Fetching one subreddit search page, then deriving an after cursor.",
        details=(
            f"subreddit: r/{SUBREDDIT}",
            f"query: {SEARCH_QUERY}",
            f"sort: {SEARCH_SORT}",
            f"limit: {SEARCH_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    console.demo_step(
        "Observed Search Cursor Evidence",
        "The derived cursor drives the second search request when available.",
        details=(
            f"derived cursor: {evidence['after_cursor']}",
            f"page 1 count: {evidence['page1_count']}",
            f"page 2 count: {evidence['page2_count']}",
            f"page 1 first title: {evidence['page1_first']}",
            f"page 2 first title: {evidence['page2_first']}",
            f"duplicate titles across pages: {evidence['duplicate_titles_count']}",
        ),
    )
    console.print(evidence)
    if not evidence["after_cursor_present"]:
        msg = "Expected to derive an after cursor from the first search page."
        raise RuntimeError(msg)
    console.demo_outcome("Search pagination produced second-page evidence.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "after_cursor_present": true,
  "duplicate_titles_count": 0,
  "page1_count": 3,
  "page2_count": 3
}
""".strip()
