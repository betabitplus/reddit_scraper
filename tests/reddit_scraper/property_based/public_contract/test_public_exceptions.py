"""Public exception taxonomy contract properties.

Why:
    Protects the caller-facing error hierarchy exposed from the root package.

Covers:
    Area: public contract
    Behavior: stable exception inheritance and context fields
    Interface: public `RedditScraper*Error` classes

Checks:
    If a public exception class is exported, then it subclasses the base error.
    If validation errors are constructed, then field/value/reason context is preserved.
"""

from __future__ import annotations

from hypothesis import given, strategies as st

import reddit_scraper

# =============================================================================
# Strategies
# =============================================================================

_PUBLIC_ERROR_TYPES = st.sampled_from(
    [
        reddit_scraper.RedditScraperConfigurationError,
        reddit_scraper.RedditScraperProviderError,
        reddit_scraper.RedditScraperRateLimitError,
        reddit_scraper.RedditScraperRequestError,
        reddit_scraper.RedditScraperResponseParseError,
        reddit_scraper.RedditScraperUnexpectedResponseError,
        reddit_scraper.RedditScraperUsageError,
        reddit_scraper.RedditScraperValidationError,
    ]
)
_SAFE_TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
    min_size=1,
    max_size=32,
)
_VALUES = st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=32))


# =============================================================================
# Properties
# =============================================================================


@given(error_type=_PUBLIC_ERROR_TYPES)
def test_public_error_types_subclass_base_error(
    error_type: type[reddit_scraper.RedditScraperError],
) -> None:
    """Generated public error types should stay within the base taxonomy."""
    assert issubclass(error_type, reddit_scraper.RedditScraperError)


@given(field=_SAFE_TEXT, value=_VALUES, reason=_SAFE_TEXT)
def test_validation_error_preserves_context_fields(
    *,
    field: str,
    value: object,
    reason: str,
) -> None:
    """Generated validation errors should expose stable context attributes."""
    error = reddit_scraper.RedditScraperValidationError(
        field=field,
        value=value,
        reason=reason,
    )

    assert error.field == field
    assert error.value == value
    assert error.reason == reason
    assert str(error) == f"Invalid value for '{field}': {value}. {reason}"


# =============================================================================
# Tests
# =============================================================================


def test_base_error_preserves_message_cause_and_context() -> None:
    """The base public error should keep caller-visible message context."""
    cause = RuntimeError("network failed")
    error = reddit_scraper.RedditScraperError(
        "custom message",
        cause=cause,
        operation="search",
    )

    assert str(error) == "custom message"
    assert error.cause is cause
    assert error.context == {"operation": "search"}
