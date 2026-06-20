# %%
"""Workbench scenario: proxy abort with direct retry for a Reddit image.

Why:
    Proves the workbench media downloader can discover a live Reddit image,
    abort a proxied stream after a tiny threshold, and retry the same URL
    directly.

Covers:
    Area: media
    Behavior: Reddit image discovery, proxy stream abort, and direct retry
    Interface: live subreddit listing JSON plus `download_url`

Checks:
    If no HTTP proxy is configured, then the script reports the prerequisite.
    If a Reddit image URL is discovered, then that URL is used for the transfer.
    If the proxied image exceeds the threshold, then proxy abort evidence is recorded.
    If proxy abort occurs, then the image is retried through a direct route.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.media.proxy_abort_direct_retry
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.media.proxy_abort_direct_retry
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
from workbench.reddit_scraper.media._media_core import (
    MediaItem,
    download_url,
    image_download_config,
)

# =============================================================================
# Scenario
# =============================================================================

SUBREDDIT = "pics"
POSTS_LIMIT = 10
POSTS_CATEGORY = "hot"
PROXY_THRESHOLD_MB = 0.0005
MAX_FILE_SIZE_MB = 10.0


# =============================================================================
# Helpers
# =============================================================================


def _item_evidence(item: MediaItem | None) -> dict[str, Any]:
    """Return small downloaded-item evidence without printing image bytes."""
    if item is None:
        return {"downloaded": False}
    return {
        "downloaded": True,
        "extension": item.extension,
        "size_bytes": item.size_bytes,
        "from_cache": item.from_cache,
    }


def _discover_image_post(*, proxy: str | None) -> dict[str, Any] | None:
    """Return the first live subreddit post with downloadable image evidence."""
    posts = _fetch_subreddit_posts(proxy=proxy)
    for post in posts:
        if post.get("image_url") or post.get("thumbnail_url"):
            return post
    return None


def _fetch_subreddit_posts(
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch the real Reddit listing used to discover proxy-download input."""
    payload = fetch_json(
        f"{REDDIT_BASE_URL}/r/{SUBREDDIT}/{POSTS_CATEGORY}.json",
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
    """Run a live proxy abort and direct retry probe when a proxy is available."""
    if not proxy:
        return {
            "proxy_prerequisite_met": False,
            "message": "Set HTTP_PROXY or HTTPS_PROXY to exercise proxy abort.",
        }

    post = _discover_image_post(proxy=proxy)
    if post is None:
        return {
            "proxy_prerequisite_met": True,
            "image_found": False,
            "message": f"No image URL found in r/{SUBREDDIT} {POSTS_CATEGORY}.",
        }

    image_url = str(post.get("image_url") or post.get("thumbnail_url"))
    config = image_download_config(
        cache_media=False,
        skip_head=True,
        use_proxy_for_small=True,
        use_proxy_for_large=False,
        proxy_size_threshold_mb=PROXY_THRESHOLD_MB,
        max_file_size_mb=MAX_FILE_SIZE_MB,
    )
    evidence = download_url(
        image_url,
        config=config,
        proxy=proxy,
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    return {
        "proxy_prerequisite_met": True,
        "image_found": True,
        "title": post.get("title"),
        "url": image_url,
        "permalink": post.get("permalink") or post.get("link"),
        "item": _item_evidence(evidence.item),
        "stats": evidence.stats,
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
        "Discovering one Reddit image, then downloading it through a tiny "
        "proxy threshold.",
        details=(
            f"subreddit: r/{SUBREDDIT}",
            f"limit: {POSTS_LIMIT}",
            f"threshold_mb: {PROXY_THRESHOLD_MB}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    if evidence["proxy_prerequisite_met"] is False:
        console.demo_skip(str(evidence["message"]))
        return
    if evidence["image_found"] is False:
        console.demo_skip(str(evidence["message"]))
        return

    console.demo_step(
        "Observed Retry",
        "The discovered Reddit image shows whether proxy abort and direct retry ran.",
        details=(
            f"title: {evidence['title']}",
            f"image URL: {evidence['url']}",
            f"downloaded: {evidence['item']['downloaded']}",
            f"size bytes: {evidence['item'].get('size_bytes')}",
            f"proxy aborts: {evidence['stats']['proxy_aborts']}",
            f"direct downloads: {evidence['stats']['direct_downloads']}",
        ),
    )
    console.print(evidence)
    stats = evidence["stats"]
    if stats["proxy_aborts"] <= 0 or stats["direct_downloads"] <= 0:
        msg = "Expected proxy abort evidence followed by a direct retry."
        raise RuntimeError(msg)
    console.demo_outcome("Proxy abort and direct retry evidence is visible.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run without HTTP_PROXY/HTTPS_PROXY:
Demo Skipped
Set HTTP_PROXY or HTTPS_PROXY to exercise proxy abort.

Real run with proxy:
{
  "image_found": true,
  "stats": {
    "direct_downloads": 1,
    "proxy_aborts": 1
  }
}
""".strip()
