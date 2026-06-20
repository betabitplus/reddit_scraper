# %%
"""Low-level Reddit JSON primitives for workbench scenarios.

Why:
    Keeps provider-shaped HTTP and reusable listing primitives in workbench so
    feature probes can stay independent from the shipped runtime.
"""

from __future__ import annotations

import html
import os
from typing import Any
from urllib.parse import urljoin

import httpx

REDDIT_BASE_URL = "https://www.reddit.com"
DEFAULT_TIMEOUT_SECONDS = 15.0
USER_AGENT = "reddit-scraper-workbench/0.1"
_THUMBNAIL_SENTINELS = {"", "self", "default", "nsfw", "spoiler"}


# =============================================================================
# HTTP
# =============================================================================


def get_proxy() -> str | None:
    """Read the optional live-run proxy from the process environment."""
    return os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


def fetch_json(
    url: str,
    *,
    params: dict[str, object] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    proxy: str | None = None,
) -> Any:
    """Fetch one live JSON document from Reddit."""
    client_kwargs: dict[str, Any] = {
        "headers": {"User-Agent": USER_AGENT},
        "follow_redirects": True,
        "timeout": timeout,
    }
    if proxy:
        client_kwargs["proxy"] = proxy

    with httpx.Client(**client_kwargs) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def reddit_url(value: object) -> str:
    """Normalize a Reddit-relative URL into a full URL."""
    if not isinstance(value, str) or not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return urljoin(REDDIT_BASE_URL, value)


# =============================================================================
# Listing Parsing
# =============================================================================


def listing_children(payload: object) -> list[dict[str, Any]]:
    """Return listing children from a Reddit listing payload."""
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    children = data.get("children")
    if not isinstance(children, list):
        return []
    return [item for item in children if isinstance(item, dict)]


def listing_after(payload: object) -> str | None:
    """Return the listing after-cursor when Reddit provides one."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    after = data.get("after")
    return after if isinstance(after, str) and after else None


def normalize_post(post_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize one Reddit post payload for workbench evidence."""
    permalink = post_data.get("permalink")
    post_url = post_data.get("url")
    result: dict[str, Any] = {
        "title": post_data.get("title"),
        "author": post_data.get("author"),
        "subreddit": post_data.get("subreddit"),
        "permalink": permalink,
        "link": reddit_url(permalink),
        "url": post_url,
        "score": post_data.get("score"),
        "num_comments": post_data.get("num_comments"),
        "created_utc": post_data.get("created_utc"),
    }

    image_url = _extract_image_url(post_data)
    if image_url:
        result["image_url"] = image_url

    thumbnail = post_data.get("thumbnail")
    if isinstance(thumbnail, str) and thumbnail not in _THUMBNAIL_SENTINELS:
        result["thumbnail_url"] = html.unescape(thumbnail)

    return result


def _extract_image_url(post_data: dict[str, Any]) -> str | None:
    """Extract a primary image URL from Reddit post data."""
    url = post_data.get("url")
    if post_data.get("post_hint") == "image" and isinstance(url, str):
        return html.unescape(url)

    source_url = _preview_source_url(post_data)
    if source_url is not None:
        return html.unescape(source_url)
    return None


def _preview_source_url(post_data: dict[str, Any]) -> str | None:
    """Return the source URL from Reddit preview image data."""
    preview = post_data.get("preview", {})
    if not isinstance(preview, dict):
        return None
    images = preview.get("images", [])
    if not images or not isinstance(images, list):
        return None
    first = images[0]
    if not isinstance(first, dict):
        return None
    source = first.get("source", {})
    if not isinstance(source, dict):
        return None
    source_url = source.get("url")
    if not isinstance(source_url, str):
        return None
    return source_url
