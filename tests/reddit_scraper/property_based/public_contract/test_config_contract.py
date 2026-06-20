"""Public config snapshot property tests.

Why:
    Protects the public config contract with property-based routing in the same
    tree shape used by mature py libraries.
"""

from __future__ import annotations

from hypothesis import given, strategies as st

from reddit_scraper import RedditScraperConfig, get_reddit_scraper_config

# =============================================================================
# Properties
# =============================================================================


@given(st.none())
def test_explicit_config_snapshot_round_trips(value: None) -> None:
    """Hypothesis inputs do not change explicit config snapshot identity."""
    _ = value
    config = RedditScraperConfig()

    assert get_reddit_scraper_config(config) is config
