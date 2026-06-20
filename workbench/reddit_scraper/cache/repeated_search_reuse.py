# %%
"""Workbench scenario: repeated search cache reuse.

Why:
    Proves the core API response cache behavior with direct Reddit JSON
    requests, independent from the shipped scraper runtime.

Covers:
    Area: cache
    Behavior: equivalent search requests populate and reuse a cache entry
    Interface: local workbench cache around live `search.json`

Checks:
    If the cache starts empty, then the first search stores one response entry.
    If the same search runs again, then the second response comes from cache.
    If cached data is reused, then normalized result counts stay stable.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.cache.repeated_search_reuse
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.cache.repeated_search_reuse
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
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

SEARCH_QUERY = "python programming"
SEARCH_LIMIT = 3
CACHE_DIR = Path(__file__).parent / ".api_cache"


# =============================================================================
# Helpers
# =============================================================================


def _search_params() -> dict[str, object]:
    """Return the fixed request shape that defines cache equivalence."""
    return {
        "limit": SEARCH_LIMIT,
        "q": SEARCH_QUERY,
        "raw_json": 1,
        "sort": "relevance",
        "type": "link",
    }


def _cache_key(url: str, params: dict[str, object]) -> str:
    """Build a stable key from the provider request shape."""
    cache_input = json.dumps(
        {"params": params, "url": url},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(cache_input.encode("utf-8")).hexdigest()


def _cache_path(cache_dir: Path, url: str, params: dict[str, object]) -> Path:
    """Return the file path for one cached provider response."""
    return cache_dir / f"{_cache_key(url, params)}.json"


def _entry_count(cache_dir: Path) -> int:
    """Count cached response files."""
    if not cache_dir.exists():
        return 0
    return len(list(cache_dir.glob("*.json")))


def _fetch_cached_search(
    *,
    cache_dir: Path,
    proxy: str | None,
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch one search through the isolated workbench cache."""
    url = f"{REDDIT_BASE_URL}/search.json"
    params = _search_params()
    path = _cache_path(cache_dir, url, params)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _extract_search_results(payload), True

    payload = fetch_json(
        url,
        params=params,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        proxy=proxy,
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return _extract_search_results(payload), False


def _extract_search_results(payload: object) -> list[dict[str, Any]]:
    """Normalize cached or live post search results for this cache scenario."""
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
    """Return compact post evidence for the cached search payload."""
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


def run_pipeline(
    *,
    cache_dir: Path = CACHE_DIR,
    proxy: str | None = None,
) -> dict[str, Any]:
    """Run the isolated repeated-search cache behavior."""
    shutil.rmtree(cache_dir, ignore_errors=True)
    entries_before = _entry_count(cache_dir)

    first_results, first_from_cache = _fetch_cached_search(
        cache_dir=cache_dir,
        proxy=proxy,
    )
    entries_after_first = _entry_count(cache_dir)

    second_results, second_from_cache = _fetch_cached_search(
        cache_dir=cache_dir,
        proxy=proxy,
    )
    entries_after_second = _entry_count(cache_dir)

    return {
        "first_count": len(first_results),
        "second_count": len(second_results),
        "entries_before": entries_before,
        "entries_after_first": entries_after_first,
        "entries_after_second": entries_after_second,
        "first_from_cache": first_from_cache,
        "second_from_cache": second_from_cache,
        "samples": _summarize_posts(first_results[:2]),
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
        "Clearing a local workbench cache, then running the same search twice.",
        details=(
            f"query: {SEARCH_QUERY}",
            f"limit: {SEARCH_LIMIT}",
            f"cache_dir: {CACHE_DIR}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    samples = evidence["samples"]
    first_sample = samples[0] if samples else {}
    console.demo_step(
        "Observed Cache Evidence",
        "The first request stores a response and the second request reuses it.",
        details=(
            f"entries: {evidence['entries_before']} -> "
            f"{evidence['entries_after_first']} -> "
            f"{evidence['entries_after_second']}",
            f"first request from cache: {evidence['first_from_cache']}",
            f"second request from cache: {evidence['second_from_cache']}",
            f"result counts: {evidence['first_count']} then {evidence['second_count']}",
            f"cached sample title: {first_sample.get('title')}",
        ),
    )
    console.print(evidence)
    if not evidence["second_from_cache"]:
        msg = "Expected the repeated search to read from cache."
        raise RuntimeError(msg)
    console.demo_outcome("Repeated equivalent searches reused one cache entry.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "entries_after_first": 1,
  "entries_after_second": 1,
  "entries_before": 0,
  "first_count": 3,
  "second_count": 3,
  "second_from_cache": true
}
""".strip()
