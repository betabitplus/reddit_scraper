# %%
"""Reddit media scenario: on-demand image download.

Why:
    Verifies that a discovered image URL can be downloaded through the public
    media downloader and reused from cache on a repeat request.

Covers:
    Area: media
    Behavior: on-demand image download and cache reuse
    Interface: `fetch_subreddit_posts` and `MediaDownloader.download`

Checks:
    If an image URL is discovered, then download status and first-cache state
    match the committed snapshot.
    If the same image is downloaded twice, then cache-hit evidence matches the
    committed snapshot.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.media.test_on_demand_download_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/media/test_on_demand_download_pipeline.py
"""

from __future__ import annotations

import os
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from IPython.display import Image, Markdown, display
from py_lib_tooling import (
    console,
    require_vcr_cassette_or_record_mode,
)
from syrupy.assertion import SnapshotAssertion

import reddit_scraper
from reddit_scraper import MediaConfig, MediaDownloader, get_default_media_config

pytestmark = [
    pytest.mark.hermetic,
    pytest.mark.vcr,
]

# =============================================================================
# Scenario
# =============================================================================
CLIENT_TIMEOUT = 15
SUBREDDIT = "pics"
POSTS_LIMIT = 10
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
MEDIA_CACHE_DIR = Path(__file__).parent / ".media_cache"


# =============================================================================
# Helpers
# =============================================================================


def get_proxy() -> str | None:
    """Get proxy from environment variable (demo-only)."""
    return os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


def find_image_url(scraper: reddit_scraper.RedditScraper) -> tuple[str | None, str]:
    """Find a post with an image URL."""
    posts = scraper.fetch_subreddit_posts(
        SUBREDDIT,
        options=reddit_scraper.SubredditPostsOptions(
            limit=POSTS_LIMIT,
            category="hot",
        ),
    )
    if not posts:
        return None, ""

    for post in posts:
        url = post.get("image_url") or post.get("thumbnail_url")
        title = post.get("title", "Untitled")
        if url:
            return url, title

    return None, ""


# =============================================================================
# Pipeline
# =============================================================================


def load_inputs() -> dict:
    """Load inputs for the pipeline."""
    return {
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def _build_media_config(**overrides: object) -> MediaConfig:
    return replace(get_default_media_config(), **overrides)


def run_pipeline(
    proxy: str | None,
    timeout: int,
    download_dir: Path = DOWNLOAD_DIR,
    media_cache_dir: Path = MEDIA_CACHE_DIR,
) -> dict:
    """Run on-demand download pipeline."""
    result: dict[str, object] = {}

    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        image_url, title = find_image_url(scraper)

    result["image_found"] = image_url is not None
    result["image_url"] = image_url
    result["image_title"] = title

    if image_url:
        shutil.rmtree(media_cache_dir, ignore_errors=True)
        result["cache_cleared"] = True

        config = _build_media_config(
            enabled=True,
            allowed_types={"image"},
            max_file_size_mb=10.0,
            cache_media=True,
            use_proxy_for_small=bool(proxy),
            use_proxy_for_large=False,
        )
        with MediaDownloader(
            config=config, proxy=proxy, cache_dir=media_cache_dir
        ) as downloader:
            item = downloader.download(image_url)
            result["downloaded"] = item is not None
            result["download_size"] = item.size_bytes if item else None
            result["from_cache"] = item.from_cache if item else None

            if item:
                download_dir.mkdir(exist_ok=True)
                safe_title = "".join(
                    c if c.isalnum() or c in " -_" else "" for c in title
                )[:30]
                filename = f"{safe_title}{item.extension}"
                filepath = download_dir / filename
                with filepath.open("wb") as file_handle:
                    file_handle.write(item.content)
                result["saved_path"] = str(filepath)

            item2 = downloader.download(image_url)
            result["cache_first"] = item.from_cache if item else None
            result["cache_second"] = item2.from_cache if item2 else None
            result["cache_first_downloaded"] = item is not None
            result["cache_second_downloaded"] = item2 is not None
            result["cache_hits"] = downloader.stats().get("cache_hits")

    return result


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    return {
        "image_found": response.get("image_found"),
        "downloaded": response.get("downloaded"),
        "from_cache": response.get("from_cache"),
        "cache_first": response.get("cache_first"),
        "cache_second": response.get("cache_second"),
        "cache_hits": response.get("cache_hits"),
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


def test_on_demand_download_pipeline_hermetic(
    snapshot: SnapshotAssertion,
    tmp_path: Path,
) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_on_demand_download_pipeline_hermetic"
    )
    inputs = load_inputs()
    inputs["download_dir"] = tmp_path / "downloads"
    inputs["media_cache_dir"] = tmp_path / "media_cache"
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live on-demand media download demo."""
    console.rule("[header]TEST: On-Demand Media Download[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    response.get("cache_first")
    cache_second = response.get("cache_second")
    cache_hits = response.get("cache_hits") or 0
    cache_first_ok = response.get("cache_first_downloaded") is True
    cache_second_ok = response.get("cache_second_downloaded") is True
    cache_probe_ok = (
        cache_first_ok and cache_second_ok and (cache_second is True or cache_hits > 0)
    )
    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Find an image post, download it, and prove cache reuse.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Subreddit:[/key] [value]{SUBREDDIT}[/value]")
    console.print(f"[key]Limit:[/key] [value]{POSTS_LIMIT}[/value]")
    console.print(f"[key]Timeout:[/key] [value]{CLIENT_TIMEOUT}s[/value]")
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Locate a post with an image URL")
    console.print("[key]2)[/key] Clear cache for that image URL")
    console.print("[key]3)[/key] Download the image (expect cache miss)")
    console.print("[key]4)[/key] Download the same image again (expect cache hit)")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        f"[key]Found image post:[/key] [value]{response.get('image_found')}[/value]"
    )
    console.print(
        f"[key]Downloaded file:[/key] [value]{response.get('downloaded')}[/value]"
    )
    console.print(
        f"[key]Size (bytes):[/key] [value]{response.get('download_size')}[/value]"
    )
    console.print(
        "[key]First download from cache:[/key] "
        f"[value]{response.get('from_cache')}[/value]"
    )
    console.print(
        f"[key]Second download from cache:[/key] [value]{cache_second}[/value]"
    )
    console.print(f"[key]Cache hits recorded:[/key] [value]{cache_hits}[/value]")
    console.print(
        f"[key]Cache reused:[/key] [value]{'yes' if cache_probe_ok else 'no'}[/value]"
    )
    console.print(
        "[key]Cache cleared for URL:[/key] "
        f"[value]{response.get('cache_cleared')}[/value]"
    )
    console.print(f"[key]Saved file:[/key] [value]{response.get('saved_path')}[/value]")

    console.rule("[subheader]Examples[/subheader]")
    console.print(f"[key]Title:[/key] [value]{response.get('image_title')}[/value]")
    console.print(f"[key]Image URL:[/key] [value]{response.get('image_url')}[/value]")
    if response.get("saved_path"):
        display(Image(filename=response["saved_path"]))
    elif response.get("image_url"):
        alt_text = response.get("image_title") or "image"
        display(Markdown(f"![{alt_text}]({response['image_url']})"))


if __name__ == "__main__":
    main()

# %%
