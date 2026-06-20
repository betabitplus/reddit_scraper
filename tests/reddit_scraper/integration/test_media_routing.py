"""Media routing integration tests.

Why:
    Protects the private media-route decision seam without teaching e2e tests
    to call private downloader methods.

Covers:
    Area: media routing
    Behavior: proxy/direct route selection
    Interface: private media-routing helper

Checks:
    If small-media proxying is enabled, then small image downloads use proxy.
    If large-media proxying is disabled, then large downloads use direct mode.
    If a URL points to video media, then it follows the large-media proxy
    policy.
"""

from __future__ import annotations

from dataclasses import replace

from reddit_scraper import get_default_media_config
from reddit_scraper._internal.media_downloader.media_routing import should_use_proxy

# =============================================================================
# Scenario
# =============================================================================

SMALL_IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/"
    "Wikipedia-logo.png/100px-Wikipedia-logo.png"
)
LARGE_FILE_URL = "https://releases.ubuntu.com/22.04/ubuntu-22.04.4-desktop-amd64.iso"
VIDEO_URL = (
    "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/"
    "Big_Buck_Bunny_360_10s_1MB.mp4"
)


# =============================================================================
# Helpers
# =============================================================================


def _proxy_routing_config():
    return replace(
        get_default_media_config(),
        enabled=True,
        use_proxy_for_small=True,
        use_proxy_for_large=False,
        proxy_size_threshold_mb=2.0,
    )


# =============================================================================
# Tests
# =============================================================================


def test_media_route_selects_proxy_for_small_files_when_enabled() -> None:
    """Keep small-media proxy routing stable for configured proxy users."""
    config = _proxy_routing_config()
    assert should_use_proxy(SMALL_IMAGE_URL, estimated_size_mb=0.1, config=config)


def test_media_route_selects_direct_for_large_files_when_large_proxy_disabled() -> None:
    """Keep large-media direct routing stable when large proxying is disabled."""
    config = _proxy_routing_config()
    assert not should_use_proxy(LARGE_FILE_URL, estimated_size_mb=700.0, config=config)


def test_media_route_treats_video_as_large_media() -> None:
    """Keep video routing tied to the large-media proxy policy."""
    config = _proxy_routing_config()
    assert not should_use_proxy(VIDEO_URL, estimated_size_mb=None, config=config)
