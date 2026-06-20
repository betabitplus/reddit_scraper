# %%
"""Media download primitives for workbench scenarios.

Why:
    Keeps binary download, cache, and routing probes independent from the
    shipped media downloader while preserving the same core behavior questions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from workbench.reddit_scraper._reddit_json import DEFAULT_TIMEOUT_SECONDS, USER_AGENT

# =============================================================================
# Constants
# =============================================================================

_IMAGE_EXTENSIONS = (".bmp", ".jpeg", ".jpg", ".png", ".tiff", ".webp")
_GIF_EXTENSIONS = (".gif", ".gifv")
_VIDEO_EXTENSIONS = (".mov", ".mp4", ".webm")
_CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}


# =============================================================================
# Models
# =============================================================================


@dataclass(frozen=True, slots=True)
class MediaConfig:
    """Configuration for one isolated workbench media run."""

    allowed_extensions: tuple[str, ...] = _IMAGE_EXTENSIONS
    max_file_size_mb: float = 5.0
    cache_media: bool = True
    skip_head: bool = False
    use_proxy_for_small: bool = True
    use_proxy_for_large: bool = False
    proxy_size_threshold_mb: float = 2.0


@dataclass(slots=True)
class MediaItem:
    """Downloaded media evidence for workbench demos."""

    url: str
    content: bytes
    content_type: str
    extension: str
    size_bytes: int
    from_cache: bool = False
    timestamp: str | None = None


@dataclass(slots=True)
class DownloadEvidence:
    """Return value for one workbench media download."""

    item: MediaItem | None
    stats: dict[str, Any]


def image_download_config(**overrides: object) -> MediaConfig:
    """Build a media config for image-focused workbench probes."""
    values: dict[str, object] = {"allowed_extensions": _IMAGE_EXTENSIONS}
    values.update(overrides)
    return MediaConfig(**values)


def media_stats(config: MediaConfig, **overrides: object) -> dict[str, Any]:
    """Return public-style media counters for manual evidence."""
    stats: dict[str, Any] = {
        "cache_hits": 0,
        "direct_downloads": 0,
        "download_count": 0,
        "proxy_aborts": 0,
        "proxy_downloads": 0,
        "proxy_threshold_mb": config.proxy_size_threshold_mb,
        "skipped_size": 0,
        "skipped_type": 0,
    }
    stats.update(overrides)
    return stats


# =============================================================================
# Public Helpers
# =============================================================================


def download_url(
    url: str,
    *,
    config: MediaConfig,
    cache_dir: Path | None = None,
    proxy: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> DownloadEvidence:
    """Download one URL with size/type checks and optional file cache."""
    stats = media_stats(config)

    if cache_dir is not None and config.cache_media:
        cached = _read_cached(cache_dir, url)
        if cached is not None:
            stats["cache_hits"] = 1
            return DownloadEvidence(item=cached, stats=stats)

    estimated_size_mb = (
        None
        if config.skip_head
        else _estimate_size_mb(
            url,
            config=config,
            proxy=proxy,
            timeout=timeout,
        )
    )
    use_proxy = bool(proxy) and _should_use_proxy(
        url,
        estimated_size_mb=estimated_size_mb,
        config=config,
    )

    item, route_stats, reason = _download_live(
        url,
        config=config,
        proxy=proxy,
        timeout=timeout,
        use_proxy=use_proxy,
    )
    stats.update(route_stats)
    if reason == "abort_proxy" and use_proxy and not config.use_proxy_for_large:
        retry_item, retry_stats, retry_reason = _download_live(
            url,
            config=config,
            proxy=None,
            timeout=timeout,
            use_proxy=False,
        )
        stats["proxy_aborts"] = 1
        stats.update(
            {
                "direct_downloads": stats["direct_downloads"]
                + retry_stats["direct_downloads"],
                "skipped_size": stats["skipped_size"] + retry_stats["skipped_size"],
                "skipped_type": stats["skipped_type"] + retry_stats["skipped_type"],
            }
        )
        item = retry_item
        reason = retry_reason

    if item is not None:
        stats["download_count"] = 1
        item.timestamp = datetime.now(UTC).isoformat()
        if cache_dir is not None and config.cache_media:
            _write_cached(cache_dir, item)
    elif reason == "skip_size":
        stats["skipped_size"] = stats["skipped_size"] + 1
    elif reason == "skip_type":
        stats["skipped_type"] = stats["skipped_type"] + 1

    return DownloadEvidence(item=item, stats=stats)


def save_media_file(item: MediaItem, *, download_dir: Path, title: str) -> Path:
    """Save a downloaded media item to a readable local filename."""
    download_dir.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(
        char if char.isalnum() or char in " -_" else "" for char in title
    )
    safe_title = safe_title.strip()[:30] or "downloaded-media"
    path = download_dir / f"{safe_title}{item.extension}"
    path.write_bytes(item.content)
    return path


# =============================================================================
# Download Internals
# =============================================================================


def _download_live(
    url: str,
    *,
    config: MediaConfig,
    proxy: str | None,
    timeout: float,
    use_proxy: bool,
) -> tuple[MediaItem | None, dict[str, int], str]:
    """Run one live media transfer route."""
    route_stats = {
        "direct_downloads": 0,
        "proxy_downloads": 0,
        "skipped_size": 0,
        "skipped_type": 0,
    }
    client_kwargs: dict[str, Any] = {
        "headers": {"User-Agent": USER_AGENT},
        "follow_redirects": True,
        "timeout": timeout,
        "trust_env": False,
    }
    if use_proxy and proxy:
        client_kwargs["proxy"] = proxy

    max_bytes = _mb_to_bytes(config.max_file_size_mb)
    threshold_bytes = _mb_to_bytes(config.proxy_size_threshold_mb)

    with httpx.Client(**client_kwargs) as client:
        request = client.build_request("GET", url)
        response = client.send(request, stream=True)
        try:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            extension = _extension_from_url(url) or _extension_from_content_type(
                content_type
            )
            if extension not in config.allowed_extensions:
                route_stats["skipped_type"] = 1
                return None, route_stats, "skip_type"

            content_length = _content_length_bytes(
                response.headers.get("content-length")
            )
            if content_length is not None and content_length > max_bytes:
                route_stats["skipped_size"] = 1
                return None, route_stats, "skip_size"
            if (
                content_length is not None
                and use_proxy
                and content_length > threshold_bytes
                and not config.use_proxy_for_large
            ):
                return None, route_stats, "abort_proxy"

            chunks: list[bytes] = []
            size_bytes = 0
            for chunk in response.iter_bytes():
                if not chunk:
                    continue
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    route_stats["skipped_size"] = 1
                    return None, route_stats, "skip_size"
                if (
                    use_proxy
                    and size_bytes > threshold_bytes
                    and not config.use_proxy_for_large
                ):
                    return None, route_stats, "abort_proxy"
                chunks.append(chunk)
        finally:
            response.close()

    if use_proxy:
        route_stats["proxy_downloads"] = 1
    else:
        route_stats["direct_downloads"] = 1

    content = b"".join(chunks)
    return (
        MediaItem(
            url=url,
            content=content,
            content_type=content_type,
            extension=extension or ".bin",
            size_bytes=len(content),
        ),
        route_stats,
        "ok",
    )


def _estimate_size_mb(
    url: str,
    *,
    config: MediaConfig,
    proxy: str | None,
    timeout: float,
) -> float | None:
    """Estimate media size with a best-effort HEAD request."""
    use_proxy = bool(proxy) and config.use_proxy_for_small
    client_kwargs: dict[str, Any] = {
        "headers": {"User-Agent": USER_AGENT},
        "follow_redirects": True,
        "timeout": timeout,
        "trust_env": False,
    }
    if use_proxy and proxy:
        client_kwargs["proxy"] = proxy
    try:
        with httpx.Client(**client_kwargs) as client:
            response = client.head(url)
            content_length = _content_length_bytes(
                response.headers.get("content-length")
            )
            if content_length is not None:
                return content_length / (1024 * 1024)
    except httpx.HTTPError:
        return None
    return None


def _should_use_proxy(
    url: str,
    *,
    estimated_size_mb: float | None,
    config: MediaConfig,
) -> bool:
    """Choose proxy/direct route for one download."""
    extension = _extension_from_url(url)
    is_video = extension in _VIDEO_EXTENSIONS
    is_large = (
        estimated_size_mb is not None
        and estimated_size_mb > config.proxy_size_threshold_mb
    )
    if is_video or is_large:
        return config.use_proxy_for_large
    return config.use_proxy_for_small


# =============================================================================
# Cache Internals
# =============================================================================


def _read_cached(cache_dir: Path, url: str) -> MediaItem | None:
    """Read cached media if the file and metadata are present."""
    media_path, meta_path = _cache_paths(cache_dir, url)
    if not media_path.exists() or not meta_path.exists():
        return None
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    return MediaItem(
        url=url,
        content=media_path.read_bytes(),
        content_type=metadata.get("content_type", ""),
        extension=metadata.get("extension", ".bin"),
        size_bytes=media_path.stat().st_size,
        from_cache=True,
        timestamp=metadata.get("timestamp"),
    )


def _write_cached(cache_dir: Path, item: MediaItem) -> None:
    """Write media bytes and metadata into a tiny workbench cache."""
    media_path, meta_path = _cache_paths(cache_dir, item.url)
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_bytes(item.content)
    meta_path.write_text(
        json.dumps(
            {
                "content_type": item.content_type,
                "extension": item.extension,
                "timestamp": item.timestamp,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _cache_paths(cache_dir: Path, url: str) -> tuple[Path, Path]:
    """Return stable cache paths for one media URL."""
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{key}.bin", cache_dir / f"{key}.json"


# =============================================================================
# Format Helpers
# =============================================================================


def _extension_from_url(url: str) -> str:
    """Return a known media extension from a URL path."""
    path = urlparse(url).path.lower()
    for extension in (*_IMAGE_EXTENSIONS, *_GIF_EXTENSIONS, *_VIDEO_EXTENSIONS):
        if path.endswith(extension):
            return extension
    return ""


def _extension_from_content_type(content_type: str) -> str:
    """Return a known extension from a Content-Type header."""
    cleaned = content_type.split(";", maxsplit=1)[0].strip().lower()
    return _CONTENT_TYPE_EXTENSIONS.get(cleaned, "")


def _mb_to_bytes(value: float) -> int:
    """Convert megabytes to bytes for local size checks."""
    return int(value * 1024 * 1024)


def _content_length_bytes(value: str | None) -> int | None:
    """Parse a Content-Length header without trusting malformed server values."""
    if value is None:
        return None
    try:
        parsed = int(value.strip())
    except ValueError:
        return None
    if parsed < 0:
        return None
    return parsed
