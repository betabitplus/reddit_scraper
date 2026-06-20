"""Public package boundary unit tests.

Why:
    Protects supported top-level imports, config helpers, public errors, and
    package version metadata.
"""

from __future__ import annotations

import reddit_scraper
from reddit_scraper import (
    InvalidConfigValueError,
    RedditScraperConfig,
    RedditScraperError,
)

# =============================================================================
# Tests
# =============================================================================


def test_public_exports_resolve() -> None:
    """All supported public names are exported by the top-level package."""
    for name in reddit_scraper.__all__:
        assert hasattr(reddit_scraper, name)


def test_public_exception_is_package_specific() -> None:
    """The package exposes one public exception base."""
    assert issubclass(RedditScraperError, Exception)


def test_public_config_exports_resolve() -> None:
    """The package exposes the shared config lifecycle."""
    installed = reddit_scraper.install_reddit_scraper_config(RedditScraperConfig())

    assert reddit_scraper.get_reddit_scraper_config().__class__ is RedditScraperConfig
    assert installed.__class__ is RedditScraperConfig


def test_invalid_config_error_is_public() -> None:
    """The package exposes a config-specific public error."""
    error = InvalidConfigValueError(
        field="field",
        value={"secret": "redacted"},
        reason="bad",
    )

    assert isinstance(error, RedditScraperError)
    assert "Invalid config value for" in str(error)


def test_version_is_available() -> None:
    """The package exposes distribution metadata."""
    assert reddit_scraper.__version__
