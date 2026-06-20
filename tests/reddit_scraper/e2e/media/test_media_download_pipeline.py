# %%
"""Reddit media scenario: public download behavior.

Why:
    Verifies public media defaults, downloader stats, streaming abort handling,
    and cache reuse through replay-backed HTTP calls.

Covers:
    Area: media
    Behavior: media download, abort fallback, and cache reuse
    Interface: `MediaDownloader` and `RedditScraper.media_stats`

Checks:
    If default media settings are used, then media stats show disabled media.
    If media is enabled, then stats expose the expected public counters.
    If media is downloaded twice with cache enabled, then cache-hit evidence
    matches the committed snapshot.

Notes:
    Pure route-selection decisions live in integration tests because they use
    private media-routing helpers.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.media.test_media_download_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/media/test_media_download_pipeline.py
"""

from __future__ import annotations

import os
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
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
POST_LIMIT = 5
MEDIA_CACHE_DIR = Path(__file__).parent / ".media_cache"

ABORT_IMAGE_URL = "https://picsum.photos/200/300.jpg"
CACHE_IMAGE_URL = "https://picsum.photos/seed/cache/200/300.jpg"


# =============================================================================
# Helpers
# =============================================================================


def get_proxy() -> str | None:
    """Get proxy from environment variable (demo-only)."""
    return os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


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


def _count_label(count: int | None) -> str:
    if count is None:
        return "unknown"
    if count == 0:
        return "none"
    if count == 1:
        return "one"
    return str(count)


def _run_abort_retry_probe(proxy: str | None, media_cache_dir: Path) -> dict:
    env_http_proxy = os.environ.pop("HTTP_PROXY", None)
    env_https_proxy = os.environ.pop("HTTPS_PROXY", None)
    config_abort = _build_media_config(
        enabled=True,
        allowed_types={"image"},
        cache_media=False,
        skip_head=True,
        use_proxy_for_small=bool(proxy),
        use_proxy_for_large=False,
        proxy_size_threshold_mb=0.0005,
        max_file_size_mb=1.0,
        max_total_downloads=1,
    )

    try:
        with MediaDownloader(
            config=config_abort, cache_dir=media_cache_dir, proxy=proxy
        ) as downloader:
            item = downloader.download(ABORT_IMAGE_URL)
            stats = downloader.stats()
    finally:
        if env_http_proxy is not None:
            os.environ["HTTP_PROXY"] = env_http_proxy
        if env_https_proxy is not None:
            os.environ["HTTPS_PROXY"] = env_https_proxy

    return {
        "abort_url": ABORT_IMAGE_URL,
        "abort_downloaded": item is not None,
        "abort_download_size": item.size_bytes if item else None,
        "abort_direct_downloads": stats.get("direct_downloads"),
        "abort_proxy_downloads": stats.get("proxy_downloads"),
        "abort_proxy_aborts": stats.get("proxy_aborts"),
    }


def _run_cache_integration(media_cache_dir: Path) -> dict:
    env_http_proxy = os.environ.pop("HTTP_PROXY", None)
    env_https_proxy = os.environ.pop("HTTPS_PROXY", None)
    config_cache = _build_media_config(
        enabled=True,
        allowed_types={"image"},
        cache_media=True,
        max_total_downloads=2,
        use_proxy_for_small=False,
        use_proxy_for_large=False,
    )
    shutil.rmtree(media_cache_dir, ignore_errors=True)
    try:
        with MediaDownloader(
            config=config_cache, cache_dir=media_cache_dir
        ) as downloader4:
            first = downloader4.download(CACHE_IMAGE_URL)
            downloader4.stats()
        with MediaDownloader(
            config=config_cache, cache_dir=media_cache_dir
        ) as downloader5:
            second = downloader5.download(CACHE_IMAGE_URL)
            stats_second = downloader5.stats()
    finally:
        if env_http_proxy is not None:
            os.environ["HTTP_PROXY"] = env_http_proxy
        if env_https_proxy is not None:
            os.environ["HTTPS_PROXY"] = env_https_proxy

    return {
        "cache_first_downloaded": first is not None,
        "cache_first_size": first.size_bytes if first else None,
        "cache_second_downloaded": second is not None,
        "cache_second_from_cache": second.from_cache if second else None,
        "cache_hits": stats_second.get("cache_hits"),
        "cache_enabled": config_cache.cache_media,
    }


def run_pipeline(
    proxy: str | None,
    timeout: int,
    media_cache_dir: Path = MEDIA_CACHE_DIR,
) -> dict:
    """Run media downloader validation pipeline."""
    results: dict[str, object] = {}

    # Test 1: Media disabled by default
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        stats = scraper.media_stats()
    results["media_enabled_default"] = stats.get("enabled")

    # Stats key presence
    config_stats = _build_media_config(
        enabled=True,
        allowed_types={"image"},
        use_proxy_for_small=bool(proxy),
        use_proxy_for_large=False,
        max_total_downloads=3,
    )
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(
            proxy=proxy,
            timeout=timeout,
            media_config=config_stats,
            media_cache_dir=str(media_cache_dir),
        )
    ) as scraper:
        stats = scraper.media_stats()
        results["stats_keys_present"] = all(
            key in stats
            for key in [
                "proxy_downloads",
                "direct_downloads",
                "proxy_aborts",
                "proxy_threshold_mb",
            ]
        )

    # Abort-and-retry mechanism (streaming, size unknown upfront)
    results["abort_head_size_mb"] = None
    results.update(_run_abort_retry_probe(proxy, media_cache_dir))

    # Cache integration
    results.update(_run_cache_integration(media_cache_dir))

    return results


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    return {
        "media_enabled_default": response.get("media_enabled_default"),
        "stats_keys_present": response.get("stats_keys_present"),
        "abort_downloaded": response.get("abort_downloaded"),
        "abort_direct_downloads": response.get("abort_direct_downloads"),
        "abort_proxy_aborts": response.get("abort_proxy_aborts"),
        "cache_first_downloaded": response.get("cache_first_downloaded"),
        "cache_second_downloaded": response.get("cache_second_downloaded"),
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


def test_media_download_pipeline_hermetic(
    snapshot: SnapshotAssertion,
    tmp_path: Path,
) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_media_download_pipeline_hermetic"
    )
    inputs = load_inputs()
    inputs["media_cache_dir"] = tmp_path / "media_cache"
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def _print_demo_scenario(proxy: str | None) -> None:
    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Validate public media defaults, stats, abort behavior, "
        "and cache reuse.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")
    console.print(f"[key]Timeout:[/key] [value]{CLIENT_TIMEOUT}s[/value]")
    console.print(f"[key]Cache dir:[/key] [value]{MEDIA_CACHE_DIR}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Defaults: media should be disabled by default")
    console.print("[key]2)[/key] Stats: verify required keys exist")
    console.print(
        "[key]3)[/key] Abort/retry: unknown size → abort on proxy → retry direct"
    )
    console.print("[key]4)[/key] Cache: second download should hit cache")


def _print_abort_retry_result(response: dict) -> None:
    console.print("[info]Test 3 — Abort/retry[/info]")
    abort_downloaded = response.get("abort_downloaded")
    abort_direct = response.get("abort_direct_downloads")
    abort_proxy = response.get("abort_proxy_aborts")
    abort_proxy_downloads = response.get("abort_proxy_downloads")
    abort_head_size = response.get("abort_head_size_mb")
    if abort_head_size is None:
        console.print(
            "[value]HEAD was skipped for this test; "
            "download started without a known size.[/value]"
        )
    else:
        console.print(
            "[value]HEAD size was known; threshold checks "
            "applied before streaming.[/value]"
        )
    if abort_downloaded and (abort_proxy or 0) > 0:
        console.print(
            "[value]Proxy started the download, aborted due to the size threshold, "
            "then retried directly and saved the file.[/value]"
        )
    elif abort_downloaded and (abort_proxy_downloads or 0) > 0:
        console.print(
            "[value]Downloaded via proxy without triggering "
            "the abort threshold.[/value]"
        )
    elif abort_downloaded:
        console.print(
            "[value]Download completed directly without "
            "triggering a proxy abort.[/value]"
        )
    else:
        console.print("[value]Download did not complete; no file was saved.[/value]")
    console.print(
        "[value]Direct download attempts: "
        f"{_count_label(abort_direct)}. "
        "Proxy aborts recorded: "
        f"{_count_label(abort_proxy)}.[/value]"
    )


def _print_cache_result(response: dict) -> None:
    console.print("[info]Test 4 — Cache reuse[/info]")
    cache_hit = (response.get("cache_hits") or 0) > 0
    cache_first = response.get("cache_first_downloaded")
    cache_second_from_cache = response.get("cache_second_from_cache")
    if cache_hit or cache_second_from_cache:
        console.print(
            "[value]Second download was served from cache (no network request).[/value]"
        )
    elif not cache_first:
        console.print(
            "[value]No cache hit because the first download "
            "did not save a file.[/value]"
        )
    else:
        console.print(
            "[value]Second download still fetched from the network; "
            "cache reuse failed.[/value]"
        )
    console.print(
        "[value]Cache enabled: "
        f"{'on' if response.get('cache_enabled') else 'off'}.[/value]"
    )


def _print_demo_results(response: dict) -> None:
    console.rule("[subheader]Results[/subheader]")
    console.print("[info]Test 1 — Defaults[/info]")
    console.print(
        "[value]Media should be disabled by default. "
        "Observed: "
        f"{'disabled' if response.get('media_enabled_default') is False else 'enabled'}"
        ".[/value]"
    )

    console.print("[info]Test 2 — Stats keys[/info]")
    console.print(
        "[value]Stats keys should exist. "
        f"Observed: {response.get('stats_keys_present')}.[/value]"
    )
    _print_abort_retry_result(response)
    _print_cache_result(response)


def main() -> None:
    """Run the live media downloader demo."""
    console.rule("[header]TEST: Media Downloader[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    _print_demo_scenario(proxy)
    _print_demo_results(response)


if __name__ == "__main__":
    main()

# %%
