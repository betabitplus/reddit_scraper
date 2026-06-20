"""Public media configuration contract properties.

Why:
    Protects media configuration validation and extension derivation at the
    supported package boundary.

Covers:
    Area: public contract
    Behavior: allowed-type coercion, extension derivation, and invalid input
    Interface: `reddit_scraper.MediaConfig` and `get_default_media_config`

Checks:
    If valid media types are generated, then allowed types normalize to a tuple.
    If media extensions are derived, then they match the selected media types.
    If invalid media types are generated, then public configuration errors are raised.
"""

from __future__ import annotations

from collections.abc import Iterable

import pytest
from hypothesis import given, strategies as st

import reddit_scraper

# =============================================================================
# Strategies
# =============================================================================

_MEDIA_TYPE_VALUES = tuple(member.value for member in reddit_scraper.MediaType)
_MEDIA_TYPE_VALUE = st.sampled_from(_MEDIA_TYPE_VALUES)
_ALLOWED_TYPE_COLLECTION = st.one_of(
    st.lists(_MEDIA_TYPE_VALUE, min_size=0, max_size=5),
    st.sets(_MEDIA_TYPE_VALUE, min_size=0, max_size=5),
    st.lists(_MEDIA_TYPE_VALUE, min_size=0, max_size=5).map(tuple),
)
_POSITIVE_FLOAT = st.floats(
    min_value=1.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False,
    width=32,
)
_NONNEGATIVE_INT = st.integers(min_value=0, max_value=100)
_NONPOSITIVE_FLOAT = st.one_of(
    st.integers(max_value=0),
    st.floats(
        max_value=0,
        allow_nan=False,
        allow_infinity=False,
        width=32,
    ),
)
_NEGATIVE_INT = st.integers(max_value=-1)
_INVALID_MEDIA_TYPE = st.text(min_size=1, max_size=24).filter(
    lambda value: value not in _MEDIA_TYPE_VALUES
)


# =============================================================================
# Helpers
# =============================================================================


def _extension_union(allowed_types: Iterable[str]) -> set[str]:
    """Return the public extension union for individual media types."""
    extensions: set[str] = set()
    for media_type in set(allowed_types):
        extensions.update(
            reddit_scraper.MediaConfig(
                allowed_types=(media_type,)
            ).get_allowed_extensions()
        )
    return extensions


# =============================================================================
# Properties
# =============================================================================


@given(
    enabled=st.booleans(),
    allowed_types=_ALLOWED_TYPE_COLLECTION,
    max_file_size_mb=_POSITIVE_FLOAT,
    max_downloads_per_post=_NONNEGATIVE_INT,
    max_total_downloads=_NONNEGATIVE_INT,
    cache_media=st.booleans(),
    download_thumbnails=st.booleans(),
    skip_head=st.booleans(),
    use_proxy_for_small=st.booleans(),
    use_proxy_for_large=st.booleans(),
    proxy_size_threshold_mb=_POSITIVE_FLOAT,
)
def test_media_config_normalizes_valid_public_inputs(
    *,
    enabled: bool,
    allowed_types: list[str] | set[str] | tuple[str, ...],
    max_file_size_mb: float,
    max_downloads_per_post: int,
    max_total_downloads: int,
    cache_media: bool,
    download_thumbnails: bool,
    skip_head: bool,
    use_proxy_for_small: bool,
    use_proxy_for_large: bool,
    proxy_size_threshold_mb: float,
) -> None:
    """Generated valid media settings should normalize without losing meaning."""
    config = reddit_scraper.MediaConfig(
        enabled=enabled,
        allowed_types=allowed_types,
        max_file_size_mb=max_file_size_mb,
        max_downloads_per_post=max_downloads_per_post,
        max_total_downloads=max_total_downloads,
        cache_media=cache_media,
        download_thumbnails=download_thumbnails,
        skip_head=skip_head,
        use_proxy_for_small=use_proxy_for_small,
        use_proxy_for_large=use_proxy_for_large,
        proxy_size_threshold_mb=proxy_size_threshold_mb,
    )

    assert config.enabled is enabled
    assert isinstance(config.allowed_types, tuple)
    assert set(config.allowed_types) == set(allowed_types)
    assert config.max_file_size_mb == max_file_size_mb
    assert config.max_downloads_per_post == max_downloads_per_post
    assert config.max_total_downloads == max_total_downloads
    assert config.cache_media is cache_media
    assert config.download_thumbnails is download_thumbnails
    assert config.skip_head is skip_head
    assert config.use_proxy_for_small is use_proxy_for_small
    assert config.use_proxy_for_large is use_proxy_for_large
    assert config.proxy_size_threshold_mb == proxy_size_threshold_mb


@given(allowed_types=_ALLOWED_TYPE_COLLECTION)
def test_media_config_extensions_match_allowed_types(
    allowed_types: list[str] | set[str] | tuple[str, ...],
) -> None:
    """Generated allowed-type sets should derive stable extension sets."""
    config = reddit_scraper.MediaConfig(allowed_types=allowed_types)
    extensions = config.get_allowed_extensions()

    assert all(extension.startswith(".") for extension in extensions)
    if reddit_scraper.MediaType.ALL.value in config.allowed_types:
        assert (
            extensions
            == reddit_scraper.MediaConfig(
                allowed_types=(reddit_scraper.MediaType.ALL.value,)
            ).get_allowed_extensions()
        )
    else:
        assert extensions == _extension_union(config.allowed_types)


@given(invalid_media_type=_INVALID_MEDIA_TYPE)
def test_media_config_rejects_invalid_allowed_types(invalid_media_type: str) -> None:
    """Generated invalid media type names should fail at the public boundary."""
    with pytest.raises(
        reddit_scraper.RedditScraperConfigurationError,
        match="allowed_types",
    ):
        reddit_scraper.MediaConfig(allowed_types=(invalid_media_type,))


@given(value=_NONPOSITIVE_FLOAT)
def test_media_config_rejects_nonpositive_size_limits(value: float | int) -> None:
    """Generated nonpositive size limits should fail at construction."""
    with pytest.raises(
        reddit_scraper.RedditScraperConfigurationError,
        match="max_file_size_mb",
    ):
        reddit_scraper.MediaConfig(max_file_size_mb=value)

    with pytest.raises(
        reddit_scraper.RedditScraperConfigurationError,
        match="proxy_size_threshold_mb",
    ):
        reddit_scraper.MediaConfig(proxy_size_threshold_mb=value)


@given(value=_NEGATIVE_INT)
def test_media_config_rejects_negative_download_counts(value: int) -> None:
    """Generated negative download counters should fail at construction."""
    with pytest.raises(
        reddit_scraper.RedditScraperConfigurationError,
        match="max_downloads_per_post",
    ):
        reddit_scraper.MediaConfig(max_downloads_per_post=value)

    with pytest.raises(
        reddit_scraper.RedditScraperConfigurationError,
        match="max_total_downloads",
    ):
        reddit_scraper.MediaConfig(max_total_downloads=value)


# =============================================================================
# Tests
# =============================================================================


def test_get_default_media_config_returns_valid_public_media_config() -> None:
    """The public default-media helper should return a valid media config DTO."""
    config = reddit_scraper.get_default_media_config()

    assert isinstance(config, reddit_scraper.MediaConfig)
    assert isinstance(config.allowed_types, tuple)
    assert all(media_type in _MEDIA_TYPE_VALUES for media_type in config.allowed_types)
