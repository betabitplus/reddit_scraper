"""Routing and URL extraction helpers for the media_downloader domain."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from reddit_scraper._api.defaults import MEDIA_ALL_EXTENSIONS, MEDIA_VIDEO_EXTENSIONS
from reddit_scraper._api.types import MediaConfig

# Content-Type to extension mapping
CONTENT_TYPE_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}


def dedupe_urls(urls: list[str]) -> list[str]:
    """Deduplicate URLs while preserving order."""
    seen: set[str] = set()
    unique_urls: list[str] = []
    for media_url in urls:
        if media_url not in seen:
            seen.add(media_url)
            unique_urls.append(media_url)
    return unique_urls


def get_extension_from_url(url: str) -> str:
    """Extract file extension from URL (restricted to known media extensions)."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in MEDIA_ALL_EXTENSIONS:
        if path.endswith(ext):
            return ext
    return ""


def get_extension_from_content_type(content_type: str) -> str:
    """Get extension from Content-Type header."""
    ct = content_type.split(";", maxsplit=1)[0].strip().lower()
    return CONTENT_TYPE_MAP.get(ct, "")


def is_media_url(url: str) -> bool:
    """Check if URL looks like a media file."""
    ext = get_extension_from_url(url)
    if ext:
        return True

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    media_hosts = {"i.redd.it", "i.imgur.com", "v.redd.it", "preview.redd.it"}
    return any(host.endswith(hostname) for hostname in media_hosts)


def is_allowed_type(url: str, *, content_type: str, config: MediaConfig) -> bool:
    """Check if media type is allowed by config."""
    allowed_ext = config.get_allowed_extensions()
    ext = get_extension_from_url(url) or get_extension_from_content_type(content_type)
    return ext in allowed_ext


def should_use_proxy(
    url: str,
    *,
    estimated_size_mb: float | None,
    config: MediaConfig,
) -> bool:
    """Determine if proxy should be used for this download."""
    ext = get_extension_from_url(url)
    is_video = ext in MEDIA_VIDEO_EXTENSIONS
    is_large = (
        estimated_size_mb is not None
        and estimated_size_mb > config.proxy_size_threshold_mb
    )

    if is_video or is_large:
        return config.use_proxy_for_large
    return config.use_proxy_for_small


def _extract_primary_url(post_data: dict[str, Any]) -> list[str]:
    """Extract the primary media URL from a Reddit post payload."""
    url = post_data.get("url", "")
    if url and is_media_url(url):
        return [url]
    return []


def _extract_preview_source_url(post_data: dict[str, Any]) -> list[str]:
    """Extract a preview image URL from `post_data[preview][images]`."""
    preview = post_data.get("preview", {})
    images = preview.get("images", [])
    if not images:
        return []

    source_url = images[0].get("source", {}).get("url", "")
    if not source_url:
        return []

    return [source_url.replace("&amp;", "&")]


def _extract_reddit_video_url(post_data: dict[str, Any]) -> list[str]:
    """Extract a Reddit video fallback URL from `media`/`secure_media`."""
    media = post_data.get("media") or post_data.get("secure_media")
    if not media:
        return []

    reddit_video = media.get("reddit_video", {})
    fallback = reddit_video.get("fallback_url", "")
    if not fallback:
        return []
    return [fallback]


def _extract_thumbnail_url(post_data: dict[str, Any]) -> list[str]:
    """Extract the thumbnail URL when it is a real URL (not a sentinel)."""
    thumbnail = post_data.get("thumbnail", "")
    if thumbnail and thumbnail not in (
        "self",
        "default",
        "nsfw",
        "spoiler",
        "",
    ):
        return [thumbnail]
    return []


def _extract_gallery_urls(post_data: dict[str, Any]) -> list[str]:
    """Extract gallery media URLs from `gallery_data`/`media_metadata`."""
    gallery_data = post_data.get("gallery_data", {})
    media_metadata = post_data.get("media_metadata", {})
    if not (gallery_data and media_metadata):
        return []

    urls: list[str] = []
    items = gallery_data.get("items", [])
    for item in items:
        media_id = item.get("media_id")
        if not media_id or media_id not in media_metadata:
            continue

        meta = media_metadata[media_id]
        source = meta.get("s", {})
        gallery_url = source.get("u") or source.get("gif") or source.get("mp4")
        if gallery_url:
            urls.append(gallery_url.replace("&amp;", "&"))

    return urls


def extract_media_urls(
    post_data: dict[str, Any], *, download_thumbnails: bool
) -> list[str]:
    """Extract media URLs from Reddit post data."""
    urls: list[str] = []

    urls.extend(_extract_primary_url(post_data))
    urls.extend(_extract_preview_source_url(post_data))
    urls.extend(_extract_reddit_video_url(post_data))

    if download_thumbnails:
        urls.extend(_extract_thumbnail_url(post_data))

    urls.extend(_extract_gallery_urls(post_data))

    return dedupe_urls(urls)
