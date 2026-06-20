"""Public option DTO contract properties.

Why:
    Protects caller-facing option objects as simple immutable value carriers.

Covers:
    Area: public contract
    Behavior: explicit option value preservation and frozen DTO fields
    Interface: public option dataclasses from `reddit_scraper`

Checks:
    If callers pass explicit values, then option DTOs preserve those values.
    If callers omit optional values, then option DTO fields remain `None`.
    If an option DTO is created, then public fields cannot be reassigned.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest
from hypothesis import given, strategies as st

import reddit_scraper

# =============================================================================
# Strategies
# =============================================================================

_SAFE_TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
    min_size=1,
    max_size=32,
)
_OPTIONAL_TEXT = st.one_of(st.none(), _SAFE_TEXT)
_OPTIONAL_BOOL = st.one_of(st.none(), st.booleans())
_OPTIONAL_LIMIT = st.one_of(st.none(), st.integers(min_value=1, max_value=100))
_OPTIONAL_TIMEOUT = st.one_of(
    st.none(),
    st.floats(
        min_value=1.0,
        max_value=120.0,
        allow_nan=False,
        allow_infinity=False,
        width=32,
    ),
)
_SEARCH_TYPES = st.one_of(
    st.none(),
    st.lists(
        st.sampled_from([member.value for member in reddit_scraper.SearchType]),
        min_size=0,
        max_size=4,
    ),
)


# =============================================================================
# Properties
# =============================================================================


@given(
    proxy=_OPTIONAL_TEXT,
    timeout=_OPTIONAL_TIMEOUT,
    cache_dir=_OPTIONAL_TEXT,
    cache_enabled=_OPTIONAL_BOOL,
)
def test_client_options_preserve_explicit_values(
    *,
    proxy: str | None,
    timeout: float | None,
    cache_dir: str | None,
    cache_enabled: bool | None,
) -> None:
    """Generated client options should keep caller-provided values unchanged."""
    options = reddit_scraper.ClientOptions(
        proxy=proxy,
        timeout=timeout,
        cache_dir=cache_dir,
        cache_enabled=cache_enabled,
    )

    assert options.proxy == proxy
    assert options.timeout == timeout
    assert options.cache_dir == cache_dir
    assert options.cache_enabled == cache_enabled


@given(
    limit=_OPTIONAL_LIMIT,
    after=_OPTIONAL_TEXT,
    before=_OPTIONAL_TEXT,
    search_types=_SEARCH_TYPES,
)
def test_search_options_preserve_explicit_values(
    *,
    limit: int | None,
    after: str | None,
    before: str | None,
    search_types: list[str] | None,
) -> None:
    """Generated search options should preserve pagination and type filters."""
    options = reddit_scraper.SearchOptions(
        limit=limit,
        after=after,
        before=before,
        search_types=search_types,
    )

    assert options.limit == limit
    assert options.after == after
    assert options.before == before
    assert options.search_types == search_types


@given(
    limit=_OPTIONAL_LIMIT,
    after=_OPTIONAL_TEXT,
    before=_OPTIONAL_TEXT,
    search_types=_SEARCH_TYPES,
    sort=st.one_of(
        st.none(),
        st.sampled_from(
            [
                reddit_scraper.SortCategory.HOT.value,
                reddit_scraper.SortCategory.TOP.value,
                reddit_scraper.SortCategory.NEW.value,
                "comments",
                "relevance",
            ]
        ),
    ),
)
def test_subreddit_search_options_preserve_explicit_values(
    *,
    limit: int | None,
    after: str | None,
    before: str | None,
    search_types: list[str] | None,
    sort: str | None,
) -> None:
    """Generated subreddit search options should preserve scoped-search fields."""
    options = reddit_scraper.SubredditSearchOptions(
        limit=limit,
        after=after,
        before=before,
        search_types=search_types,
        sort=sort,
    )

    assert options.limit == limit
    assert options.after == after
    assert options.before == before
    assert options.search_types == search_types
    assert options.sort == sort


@given(
    limit=_OPTIONAL_LIMIT,
    category=st.one_of(
        st.none(),
        st.sampled_from([member.value for member in reddit_scraper.SortCategory]),
    ),
    time_filter=st.one_of(
        st.none(),
        st.sampled_from([member.value for member in reddit_scraper.TimeFilter]),
    ),
)
def test_feed_options_preserve_explicit_values(
    *,
    limit: int | None,
    category: str | None,
    time_filter: str | None,
) -> None:
    """Generated feed options should keep category and time-filter values."""
    options = reddit_scraper.FeedOptions(
        limit=limit,
        category=category,
        time_filter=time_filter,
    )

    assert options.limit == limit
    assert options.category == category
    assert options.time_filter == time_filter


@given(
    limit=_OPTIONAL_LIMIT,
    category=st.one_of(
        st.none(),
        st.sampled_from([member.value for member in reddit_scraper.SortCategory]),
    ),
    time_filter=st.one_of(
        st.none(),
        st.sampled_from([member.value for member in reddit_scraper.TimeFilter]),
    ),
    geo_filter=st.one_of(
        st.none(),
        st.sampled_from([member.value.lower() for member in reddit_scraper.GeoFilter]),
    ),
)
def test_popular_feed_options_preserve_explicit_values(
    *,
    limit: int | None,
    category: str | None,
    time_filter: str | None,
    geo_filter: str | None,
) -> None:
    """Generated popular-feed options should preserve geo filter values."""
    options = reddit_scraper.PopularFeedOptions(
        limit=limit,
        category=category,
        time_filter=time_filter,
        geo_filter=geo_filter,
    )

    assert options.limit == limit
    assert options.category == category
    assert options.time_filter == time_filter
    assert options.geo_filter == geo_filter


@given(
    limit=_OPTIONAL_LIMIT,
    category=st.one_of(
        st.none(),
        st.sampled_from(["hot", "top", "new", "userhot", "usertop", "usernew"]),
    ),
    time_filter=st.one_of(
        st.none(),
        st.sampled_from([member.value for member in reddit_scraper.TimeFilter]),
    ),
)
def test_subreddit_posts_options_preserve_explicit_values(
    *,
    limit: int | None,
    category: str | None,
    time_filter: str | None,
) -> None:
    """Generated subreddit listing options should preserve public feed fields."""
    options = reddit_scraper.SubredditPostsOptions(
        limit=limit,
        category=category,
        time_filter=time_filter,
    )

    assert options.limit == limit
    assert options.category == category
    assert options.time_filter == time_filter


# =============================================================================
# Tests
# =============================================================================


def test_public_option_dtos_are_frozen() -> None:
    """Option DTO fields should not be reassigned after construction."""
    options = reddit_scraper.SearchOptions(limit=10)

    with pytest.raises(FrozenInstanceError):
        options.limit = 20


def test_install_reddit_scraper_config_replaces_active_public_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public config install helper should replace later default resolution."""
    original = reddit_scraper.get_reddit_scraper_config()
    updated_limit = 37 if original.defaults.feed.limit != 37 else 38
    updated = replace(
        original,
        defaults=replace(
            original.defaults,
            feed=replace(original.defaults.feed, limit=updated_limit),
        ),
    )
    seen_limits: list[int | None] = []

    class FakeScraper:
        def fetch_frontpage(
            self,
            *,
            options: reddit_scraper.FeedOptions,
        ) -> list[object]:
            seen_limits.append(options.limit)
            return []

    def fake_get_reddit_scraper_service(*, client: object = None) -> FakeScraper:
        _ = client
        return FakeScraper()

    monkeypatch.setitem(
        reddit_scraper.fetch_frontpage.__globals__,
        "get_reddit_scraper_service",
        fake_get_reddit_scraper_service,
    )
    reddit_scraper.fetch_frontpage()

    try:
        installed = reddit_scraper.install_reddit_scraper_config(updated)
        current = reddit_scraper.get_reddit_scraper_config()
        reddit_scraper.fetch_frontpage()

        assert installed is updated
        assert current is updated
        assert seen_limits == [original.defaults.feed.limit, updated_limit]
    finally:
        reddit_scraper.install_reddit_scraper_config(original)


def test_install_reddit_scraper_config_rejects_non_config_objects() -> None:
    """Only the public RedditScraperConfig snapshot type should be installable."""
    with pytest.raises(TypeError, match="RedditScraperConfig instance"):
        reddit_scraper.install_reddit_scraper_config(object())
