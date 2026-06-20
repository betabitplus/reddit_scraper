# %%
"""Workbench scenario: invalid subreddit degradation.

Why:
    Proves the core provider-failure translation for an invalid subreddit
    without importing the shipped scraper runtime.

Covers:
    Area: retry
    Behavior: invalid subreddit provider response becomes empty public evidence
    Interface: live subreddit listing request with local boundary translation

Checks:
    If Reddit rejects an invalid subreddit, then empty results are returned.
    If Reddit returns an empty listing directly, then the empty result remains visible.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.retry.invalid_subreddit_empty
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.retry.invalid_subreddit_empty
"""

from __future__ import annotations

from typing import Any

import httpx
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

INVALID_SUBREDDIT = "thisdoesnotexist12345xyz"
POSTS_LIMIT = 1
RECOVERABLE_STATUS_CODES = {403, 404}


# =============================================================================
# Helpers
# =============================================================================


def _fetch_invalid_subreddit(*, proxy: str | None) -> dict[str, Any]:
    """Translate provider-side invalid subreddit responses into empty evidence."""
    try:
        posts = _fetch_subreddit_posts(proxy=proxy)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code not in RECOVERABLE_STATUS_CODES:
            raise
        return {
            "count": 0,
            "empty": True,
            "translated": True,
            "status_code": status_code,
        }

    return {
        "count": len(posts),
        "empty": not posts,
        "translated": False,
        "status_code": None,
    }


def _fetch_subreddit_posts(
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch the deliberately invalid subreddit listing."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{INVALID_SUBREDDIT}/hot.json",
        params={"limit": POSTS_LIMIT, "raw_json": 1, "t": "all"},
        timeout=timeout,
        proxy=proxy,
    )
    posts: list[dict[str, Any]] = []
    for child in listing_children(payload):
        data = child.get("data", {})
        if isinstance(data, dict):
            posts.append(normalize_post(data))
    return posts


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, proxy: str | None = None) -> dict[str, Any]:
    """Run the isolated invalid-subreddit degradation behavior."""
    return _fetch_invalid_subreddit(proxy=proxy)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the workbench script as a narrative manual demo."""
    console.demo_intro(__doc__)
    proxy = get_proxy()
    console.demo_step(
        "Scenario",
        "Requesting a deliberately invalid subreddit through a public boundary.",
        details=(
            f"subreddit: r/{INVALID_SUBREDDIT}",
            f"limit: {POSTS_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    console.demo_step(
        "Observed Degradation Evidence",
        "The invalid provider response is represented as an empty result.",
        details=(
            f"status code: {evidence['status_code']}",
            f"translated at boundary: {evidence['translated']}",
            f"result count: {evidence['count']}",
            f"empty result: {evidence['empty']}",
        ),
    )
    console.print(evidence)
    if not evidence["empty"]:
        msg = "Expected the invalid subreddit to produce an empty result."
        raise RuntimeError(msg)
    console.demo_outcome("Invalid subreddit behavior degraded to empty evidence.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "count": 0,
  "empty": true,
  "status_code": 404,
  "translated": true
}
""".strip()
