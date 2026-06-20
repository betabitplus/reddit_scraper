"""Public export and enum contract properties.

Why:
    Protects the supported root-package surface and string enum vocabulary.

Covers:
    Area: public contract
    Behavior: exported names and enum round-tripping
    Interface: `reddit_scraper.__all__` and public enum classes

Checks:
    If a name is listed in `__all__`, then the root package exposes it.
    If an enum member is generated, then its public string value round-trips.
"""

from __future__ import annotations

from enum import StrEnum

from hypothesis import given, strategies as st

import reddit_scraper

# =============================================================================
# Strategies
# =============================================================================

_PUBLIC_ENUM_MEMBERS = st.sampled_from(
    [
        *reddit_scraper.SearchType,
        *reddit_scraper.TimeFilter,
        *reddit_scraper.SortCategory,
        *reddit_scraper.GeoFilter,
        *reddit_scraper.MediaType,
    ]
)


# =============================================================================
# Properties
# =============================================================================


@given(member=_PUBLIC_ENUM_MEMBERS)
def test_public_string_enums_round_trip(member: StrEnum) -> None:
    """Generated public enum members should keep stable string semantics."""
    enum_type = type(member)

    assert isinstance(member.value, str)
    assert str(member) == member.value
    assert enum_type(member.value) is member


# =============================================================================
# Tests
# =============================================================================


def test_root_package_all_names_are_exposed() -> None:
    """The root package facade should publish every declared public name."""
    missing = [
        name for name in reddit_scraper.__all__ if not hasattr(reddit_scraper, name)
    ]

    assert missing == []


def test_root_package_all_excludes_private_names() -> None:
    """The supported facade should not advertise private implementation names."""
    private_names = [name for name in reddit_scraper.__all__ if name.startswith("_")]

    assert private_names == []
