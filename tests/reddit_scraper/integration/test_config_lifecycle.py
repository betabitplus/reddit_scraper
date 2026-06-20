"""Config lifecycle integration tests.

Why:
    Verifies that public config construction, installation, and explicit
    snapshot resolution compose without relying on private imports.
"""

from __future__ import annotations

import pytest

from reddit_scraper import (
    RedditScraperConfig,
    get_reddit_scraper_config,
    install_reddit_scraper_config,
)

# =============================================================================
# Tests
# =============================================================================


def test_install_config_rejects_wrong_type() -> None:
    """The config lifecycle rejects unsupported config objects."""
    with pytest.raises(TypeError, match=r"install_reddit_scraper_config\(\) expects"):
        install_reddit_scraper_config(object())


def test_get_config_accepts_explicit_snapshot() -> None:
    """Explicit config snapshots can bypass the installed global snapshot."""
    config = RedditScraperConfig()

    assert get_reddit_scraper_config(config) is config
