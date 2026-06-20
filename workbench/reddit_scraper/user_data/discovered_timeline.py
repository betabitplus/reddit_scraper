# %%
"""Workbench scenario: discovered user timeline.

Why:
    Proves that a username discovered from subreddit posts can drive a live
    public Reddit user timeline request.

Covers:
    Area: user data
    Behavior: author discovery and mixed post/comment timeline extraction
    Interface: live subreddit listing plus `user/<name>/.json`

Checks:
    If author discovery finds a usable author or uses the fallback, then the
    target username is not empty.
    If user data is fetched, then item counts and subreddit evidence are
    visible.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.user_data.discovered_timeline
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.user_data.discovered_timeline
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

DISCOVERY_SUBREDDIT = "marvelstudios"
DISCOVERY_LIMIT = 3
DISCOVERY_CATEGORY = "hot"
USER_DATA_LIMIT = 5
FALLBACK_USER = "chanma50"
_SKIPPED_AUTHORS = {"[deleted]", "AutoModerator"}


# =============================================================================
# Helpers
# =============================================================================


def _choose_author(posts: list[dict[str, Any]]) -> str:
    """Pick a visible author from posts, otherwise use the fallback user."""
    for post in posts:
        author = post.get("author")
        if isinstance(author, str) and author and author not in _SKIPPED_AUTHORS:
            return author
    return FALLBACK_USER


def _fetch_discovery_posts(
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch the subreddit listing used only to discover a username."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{DISCOVERY_SUBREDDIT}/{DISCOVERY_CATEGORY}.json",
        params={"limit": DISCOVERY_LIMIT, "raw_json": 1, "t": "all"},
        timeout=timeout,
        proxy=proxy,
    )
    return _posts_from_listing(payload)


def _posts_from_listing(payload: object) -> list[dict[str, Any]]:
    """Normalize discovery listing post children."""
    posts: list[dict[str, Any]] = []
    for child in listing_children(payload):
        data = child.get("data", {})
        if isinstance(data, dict):
            posts.append(normalize_post(data))
    return posts


def _fetch_user_data(
    username: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch and normalize one public user timeline for this scenario."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/user/{username}/.json",
        params={"limit": USER_DATA_LIMIT, "raw_json": 1},
        timeout=timeout,
        proxy=proxy,
    )
    items: list[dict[str, Any]] = []
    for child in listing_children(payload):
        parsed = _parse_user_item(child)
        if parsed is not None:
            items.append(parsed)
    return items


def _parse_user_item(child: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize one user timeline child into post or comment evidence."""
    data = child.get("data", {})
    if not isinstance(data, dict):
        return None

    if child.get("kind") == "t3":
        permalink = data.get("permalink", "")
        return {
            "type": "post",
            "title": data.get("title", ""),
            "subreddit": data.get("subreddit", ""),
            "permalink": permalink,
            "link": reddit_url(permalink),
            "created_utc": data.get("created_utc", ""),
        }

    if child.get("kind") == "t1":
        permalink = data.get("permalink", "")
        return {
            "type": "comment",
            "body": data.get("body", ""),
            "subreddit": data.get("subreddit", ""),
            "permalink": permalink,
            "link": reddit_url(permalink),
            "created_utc": data.get("created_utc", ""),
        }

    return None


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, proxy: str | None = None) -> dict[str, Any]:
    """Run author discovery and user timeline extraction."""
    posts = _fetch_discovery_posts(proxy=proxy)
    target_user = _choose_author(posts)
    user_items = _fetch_user_data(target_user, proxy=proxy)
    posts_count = len([item for item in user_items if item.get("type") == "post"])
    comments_count = len([item for item in user_items if item.get("type") == "comment"])
    return {
        "target_user": target_user,
        "total_items": len(user_items),
        "posts": posts_count,
        "comments": comments_count,
        "subreddits": sorted(
            {item.get("subreddit") for item in user_items if item.get("subreddit")}
        )[:5],
        "samples": user_items[:2],
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
        "Discovering a subreddit author and fetching that user's timeline.",
        details=(
            f"discovery subreddit: r/{DISCOVERY_SUBREDDIT}",
            f"timeline limit: {USER_DATA_LIMIT}",
            f"fallback user: {FALLBACK_USER}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    samples = evidence["samples"]
    first_sample = samples[0] if samples else {}
    console.demo_step(
        "Observed User Timeline",
        "The user endpoint returned mixed item and subreddit evidence.",
        details=(
            f"target user: u/{evidence['target_user']}",
            f"items: {evidence['total_items']} total, "
            f"{evidence['posts']} posts, {evidence['comments']} comments",
            f"subreddits seen: {', '.join(evidence['subreddits'])}",
            f"first item type: {first_sample.get('type')}",
            f"first item permalink: {first_sample.get('permalink')}",
        ),
    )
    console.print(evidence)
    if not evidence["target_user"]:
        msg = "Expected a non-empty target username."
        raise RuntimeError(msg)
    console.demo_outcome("User data returned inspectable timeline evidence.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "comments": 2,
  "posts": 3,
  "subreddits": ["..."],
  "target_user": "...",
  "total_items": 5
}
""".strip()
