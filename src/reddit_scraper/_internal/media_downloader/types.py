"""Private media downloader runtime types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MediaCacheEntry:
    """Cached media metadata and content."""

    url: str
    content: bytes
    content_type: str
    extension: str
    size_bytes: int
    timestamp: str | None = None
