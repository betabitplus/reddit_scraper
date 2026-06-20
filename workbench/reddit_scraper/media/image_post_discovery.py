# %%
"""Workbench scenario: image post discovery from subreddit listings.

Why:
    Proves that live subreddit listings expose image or thumbnail evidence
    without importing the shipped scraper package.

Covers:
    Area: media
    Behavior: primary subreddit image discovery with fallback subreddit retry
    Interface: live subreddit listing JSON requests through workbench helpers

Checks:
    If the primary subreddit exposes image posts, then fallback is not used.
    If the primary has no image posts, then fallback is queried for images.
    If image posts are discovered, then samples keep image or thumbnail URLs.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.media.image_post_discovery
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.media.image_post_discovery
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

PRIMARY_SUBREDDIT = "marvelstudios"
FALLBACK_SUBREDDIT = "Marvel"
POSTS_LIMIT = 10
POSTS_CATEGORY = "hot"
MAX_IMAGES = 2


# =============================================================================
# Helpers
# =============================================================================


def _image_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return posts that expose a primary image or thumbnail URL."""
    return [
        post for post in posts if post.get("image_url") or post.get("thumbnail_url")
    ]


def _summarize_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return compact image-post evidence for console output."""
    return [
        {
            "title": post.get("title"),
            "subreddit": post.get("subreddit"),
            "image_url": post.get("image_url"),
            "thumbnail_url": post.get("thumbnail_url"),
            "permalink": post.get("permalink") or post.get("link"),
        }
        for post in posts
    ]


def _fetch_subreddit_posts(
    subreddit: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch one subreddit listing for image discovery."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{subreddit}/{POSTS_CATEGORY}.json",
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
    """Discover image posts from a primary listing with fallback behavior."""
    posts = _fetch_subreddit_posts(
        PRIMARY_SUBREDDIT,
        proxy=proxy,
    )
    source_subreddit = PRIMARY_SUBREDDIT
    image_posts = _image_posts(posts)[:MAX_IMAGES]

    if not image_posts:
        posts = _fetch_subreddit_posts(
            FALLBACK_SUBREDDIT,
            proxy=proxy,
        )
        source_subreddit = FALLBACK_SUBREDDIT
        image_posts = _image_posts(posts)[:MAX_IMAGES]

    return {
        "source_subreddit": source_subreddit,
        "fallback_used": source_subreddit == FALLBACK_SUBREDDIT,
        "image_count": len(image_posts),
        "sample_urls": [
            post.get("image_url") or post.get("thumbnail_url") for post in image_posts
        ],
        "samples": _summarize_posts(image_posts),
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
        "Fetching a primary subreddit listing and falling back only if needed.",
        details=(
            f"primary: r/{PRIMARY_SUBREDDIT}",
            f"fallback: r/{FALLBACK_SUBREDDIT}",
            f"limit: {POSTS_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    samples = evidence["samples"]
    first_sample = samples[0] if samples else {}
    console.demo_step(
        "Observed Image Posts",
        "The listing response was filtered to posts with image or thumbnail URLs.",
        details=(
            f"source subreddit: r/{evidence['source_subreddit']}",
            f"fallback used: {evidence['fallback_used']}",
            f"image posts found: {evidence['image_count']}",
            f"first title: {first_sample.get('title')}",
            f"first media URL: "
            f"{first_sample.get('image_url') or first_sample.get('thumbnail_url')}",
        ),
    )
    console.print(evidence)
    if evidence["image_count"] <= 0:
        msg = "Expected at least one image or thumbnail URL from primary/fallback."
        raise RuntimeError(msg)
    console.demo_outcome(
        "The live listing exposed image evidence through the workbench JSON path.",
    )


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "fallback_used": false,
  "image_count": 2,
  "sample_urls": ["https://...", "https://..."],
  "source_subreddit": "marvelstudios"
}
""".strip()
