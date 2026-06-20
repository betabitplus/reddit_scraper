"""Search helpers for reddit_scraper."""

from __future__ import annotations

from reddit_scraper._api.defaults import SUPPORTED_SEARCH_TYPES
from reddit_scraper._api.errors import RedditScraperValidationError


def build_type_param(search_types: list[str] | None) -> str:
    """Build the type parameter for search queries.

    Only 'link' (posts) and 'sr' (subreddits) are supported.
    """
    if not search_types:
        return "link"
    normalized: list[str] = []
    for raw_type in search_types:
        normalized_type = raw_type.lower().strip()
        if normalized_type == "post":
            normalized_type = "link"
        if normalized_type not in SUPPORTED_SEARCH_TYPES:
            raise RedditScraperValidationError(
                field="search_type",
                value=normalized_type,
                reason=f"must be one of {list(SUPPORTED_SEARCH_TYPES)}",
            )
        normalized.append(normalized_type)
    return ",".join(normalized)
