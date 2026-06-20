"""Parsing helpers for reddit_scraper."""

from __future__ import annotations

from typing import Any


def get_listing_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract listing items from a Reddit API response."""
    listing = data.get("data", {})
    items = listing.get("children", [])
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]
