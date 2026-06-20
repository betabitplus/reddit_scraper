# %%
"""Workbench scenario: on-demand download from a discovered Reddit image.

Why:
    Proves that a live Reddit image URL discovered from a subreddit listing can
    be downloaded on demand and reused from the workbench media cache.

Covers:
    Area: media
    Behavior: discovered image download and cache reuse
    Interface: live subreddit listing JSON plus `download_url`

Checks:
    If a Reddit image URL is found, then the first download returns media bytes.
    If the image URL is downloaded again, then the second download is cached.
    If a downloaded item is saved, then the saved path is visible.

Examples:
    Run manually:
        uv run python -m workbench.reddit_scraper.media.on_demand_discovered_image
        uv run py-lib-reproduce-running-loop \
            workbench.reddit_scraper.media.on_demand_discovered_image
"""

from __future__ import annotations

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
from workbench.reddit_scraper.media._media_core import (
    MediaItem,
    download_url,
    image_download_config,
    save_media_file,
)

# =============================================================================
# Scenario
# =============================================================================

SUBREDDIT = "pics"
POSTS_LIMIT = 10
POSTS_CATEGORY = "hot"
CACHE_DIR = Path(__file__).parent / ".media_cache" / "discovered"
DOWNLOAD_DIR = Path(__file__).parent / "downloads"


# =============================================================================
# Helpers
# =============================================================================


def _find_image_post(*, proxy: str | None = None) -> dict[str, Any] | None:
    """Return the first live subreddit post with image or thumbnail evidence."""
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
    """Fetch the listing used to discover an on-demand image URL."""
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


def _item_evidence(item: MediaItem | None) -> dict[str, Any]:
    """Return compact downloaded-item evidence without printing media bytes."""
    if item is None:
        return {"downloaded": False}
    return {
        "downloaded": True,
        "extension": item.extension,
        "from_cache": item.from_cache,
        "size_bytes": item.size_bytes,
    }


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(
    *,
    proxy: str | None = None,
    cache_dir: Path = CACHE_DIR,
    download_dir: Path = DOWNLOAD_DIR,
) -> dict[str, Any]:
    """Discover one Reddit image URL, download it, and prove cache reuse."""
    post = _find_image_post(proxy=proxy)
    if post is None:
        return {
            "image_found": False,
            "message": f"No image URL found in r/{SUBREDDIT} hot listing.",
        }

    image_url = post.get("image_url") or post.get("thumbnail_url")
    title = str(post.get("title") or "downloaded-media")
    shutil.rmtree(cache_dir, ignore_errors=True)

    config = image_download_config(
        cache_media=True,
        max_file_size_mb=10.0,
        use_proxy_for_small=bool(proxy),
        use_proxy_for_large=False,
    )
    first = download_url(
        str(image_url),
        config=config,
        cache_dir=cache_dir,
        proxy=proxy,
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    saved_path = None
    if first.item is not None:
        saved_path = save_media_file(first.item, download_dir=download_dir, title=title)

    second = download_url(
        str(image_url),
        config=config,
        cache_dir=cache_dir,
        proxy=proxy,
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    return {
        "image_found": True,
        "title": title,
        "image_url": image_url,
        "permalink": post.get("permalink") or post.get("link"),
        "first": _item_evidence(first.item),
        "second": _item_evidence(second.item),
        "second_stats": second.stats,
        "saved_path": str(saved_path) if saved_path is not None else None,
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
        "Discovering one Reddit image URL, downloading it, and repeating it.",
        details=(
            f"subreddit: r/{SUBREDDIT}",
            f"limit: {POSTS_LIMIT}",
            f"proxy: {'on' if proxy else 'off'}",
        ),
    )

    evidence = run_pipeline(proxy=proxy)
    if evidence["image_found"] is False:
        console.demo_skip(str(evidence["message"]))
        return

    console.demo_step(
        "Observed Download",
        "The discovered image was downloaded once and then read from cache.",
        details=(
            f"title: {evidence['title']}",
            f"image URL: {evidence['image_url']}",
            f"first download: {evidence['first']['size_bytes']} bytes, "
            f"from_cache={evidence['first']['from_cache']}",
            f"second download from cache: {evidence['second']['from_cache']}",
            f"saved path: {evidence['saved_path']}",
        ),
    )
    console.print(evidence)
    if evidence["first"]["downloaded"] is not True:
        msg = "Expected first discovered-image download to return media bytes."
        raise RuntimeError(msg)
    if evidence["second"]["from_cache"] is not True:
        msg = "Expected second discovered-image download to hit cache."
        raise RuntimeError(msg)
    if evidence.get("saved_path"):
        console.display_image_if_available(Path(str(evidence["saved_path"])))
    console.demo_outcome("The discovered Reddit image supports on-demand cache reuse.")


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
Real run:
{
  "image_found": true,
  "first": {"downloaded": true, "from_cache": false},
  "second": {"downloaded": true, "from_cache": true},
  "second_stats": {"cache_hits": 1}
}
""".strip()
