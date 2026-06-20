"""Public response DTO contract properties.

Why:
    Protects caller-visible response wrappers and their count semantics.

Covers:
    Area: public contract
    Behavior: count properties and independent default metadata containers
    Interface: public response dataclasses from `reddit_scraper`

Checks:
    If response item lists are generated, then `count` equals list length.
    If metadata or stats are omitted, then each response gets its own mapping.
"""

from __future__ import annotations

from typing import Any

from hypothesis import given, strategies as st

import reddit_scraper

# =============================================================================
# Strategies
# =============================================================================

_SAFE_KEY = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
    min_size=1,
    max_size=16,
)
_SCALAR = st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=32))
_PUBLIC_DICT = st.dictionaries(_SAFE_KEY, _SCALAR, max_size=5)
_RESULTS = st.lists(_PUBLIC_DICT, max_size=20)
_MEDIA_ITEMS = st.lists(st.one_of(_PUBLIC_DICT, _SCALAR), max_size=20)


# =============================================================================
# Properties
# =============================================================================


@given(results=_RESULTS, metadata=_PUBLIC_DICT)
def test_search_response_count_matches_results(
    *,
    results: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> None:
    """Generated search responses should count exactly their result list."""
    response = reddit_scraper.SearchResponse(results=results, metadata=metadata)

    assert response.results == results
    assert response.metadata == metadata
    assert response.count == len(results)


@given(items=_RESULTS, metadata=_PUBLIC_DICT)
def test_user_data_response_count_matches_items(
    *,
    items: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> None:
    """Generated user-data responses should count exactly their item list."""
    response = reddit_scraper.UserDataResponse(items=items, metadata=metadata)

    assert response.items == items
    assert response.metadata == metadata
    assert response.count == len(items)


@given(items=_MEDIA_ITEMS, stats=_PUBLIC_DICT)
def test_media_download_response_count_matches_items(
    *,
    items: list[Any],
    stats: dict[str, Any],
) -> None:
    """Generated media responses should count exactly their downloaded items."""
    response = reddit_scraper.MediaDownloadResponse(items=items, stats=stats)

    assert response.items == items
    assert response.stats == stats
    assert response.count == len(items)


@given(title=st.text(max_size=80), body=st.text(max_size=500), comments=_RESULTS)
def test_post_details_response_preserves_post_fields(
    *,
    title: str,
    body: str,
    comments: list[dict[str, Any]],
) -> None:
    """Generated post-detail responses should preserve caller-visible fields."""
    response = reddit_scraper.PostDetailsResponse(
        title=title,
        body=body,
        comments=comments,
    )

    assert response.title == title
    assert response.body == body
    assert response.comments == comments


# =============================================================================
# Tests
# =============================================================================


def test_response_default_mappings_are_not_shared() -> None:
    """Default metadata and stats mappings should be independent per response."""
    first_search = reddit_scraper.SearchResponse(results=[])
    second_search = reddit_scraper.SearchResponse(results=[])
    first_user = reddit_scraper.UserDataResponse(items=[])
    second_user = reddit_scraper.UserDataResponse(items=[])
    first_post = reddit_scraper.PostDetailsResponse(title="", body="", comments=[])
    second_post = reddit_scraper.PostDetailsResponse(title="", body="", comments=[])
    first_media = reddit_scraper.MediaDownloadResponse(items=[])
    second_media = reddit_scraper.MediaDownloadResponse(items=[])

    first_search.metadata["changed"] = True
    first_user.metadata["changed"] = True
    first_post.metadata["changed"] = True
    first_media.stats["changed"] = True

    assert second_search.metadata == {}
    assert second_user.metadata == {}
    assert second_post.metadata == {}
    assert second_media.stats == {}
