"""Public exceptions for `reddit_scraper`.

Why:
    Keeps the caller-facing exception taxonomy stable and separate from
    private request, retry, parsing, cache, and media details.

How:
    Runtime internals translate operational failures into these public
    exceptions before they cross the package boundary. Direct caller input
    violations may still use built-in `TypeError` or `ValueError`.
"""

from __future__ import annotations


class RedditScraperError(Exception):
    """Base exception for all errors raised by the reddit_scraper module."""

    def __init__(
        self,
        message: str | None = None,
        *,
        cause: Exception | None = None,
        **context: object,
    ) -> None:
        """Initialize the error with optional context.

        Args:
            message: Optional error message.
            cause: Optional underlying exception.
            **context: Structured context for error reporting.
        """
        self.cause = cause
        self.context = context
        if message is None and cause is not None:
            message = f"Reddit scraper failed: {cause}"
        elif message is None:
            message = "Reddit scraper failed"
        super().__init__(message)


class RedditScraperConfigurationError(RedditScraperError):
    """Base exception for configuration-related issues."""


class RedditScraperUsageError(RedditScraperError):
    """Base exception for errors related to incorrect usage of the API."""


class RedditScraperProviderError(RedditScraperError):
    """Base exception for runtime/provider errors after retries are exhausted."""

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
        url: str | None = None,
    ) -> None:
        """Initialize with a formatted message and the underlying cause."""
        self.cause = cause
        self.url = url
        super().__init__(message)


class InvalidConfigValueError(RedditScraperConfigurationError):
    """Raised when a specific value in the reddit_scraper config is invalid."""

    def __init__(self, *, field: str, value: object, reason: str) -> None:
        """Initialize with field, value, and reason."""
        self.field = field
        self.value = value
        self.reason = reason
        message = f"Invalid config value for '{field}': {value}. {reason}"
        super().__init__(message)


class CacheError(RedditScraperProviderError):
    """Raised when media cache operations fail."""

    def __init__(self, *, operation: str, url: str, cause: Exception) -> None:
        """Initialize with cache operation context."""
        self.operation = operation
        self.url = url
        self.cause = cause
        message = f"Media cache {operation} failed for '{url}'."
        super().__init__(message, cause=cause, url=url)


class RedditScraperValidationError(RedditScraperUsageError):
    """Raised for caller input validation errors."""

    def __init__(
        self,
        *,
        field: str,
        value: object,
        reason: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize with field, value, reason, and optional cause."""
        self.field = field
        self.value = value
        self.reason = reason
        message = f"Invalid value for '{field}': {value}. {reason}"
        super().__init__(message=message, cause=cause)


class RedditScraperRequestError(RedditScraperProviderError):
    """Raised when a Reddit request fails after retries."""

    def __init__(self, *, url: str, cause: Exception) -> None:
        """Initialize with URL context and underlying cause."""
        self.url = url
        self.cause = cause
        message = (
            f"Request to '{self.url}' failed after retries. "
            f"Original error: {self.cause}"
        )
        super().__init__(message, cause=cause, url=url)


class RedditScraperRateLimitError(RedditScraperProviderError):
    """Raised when rate limited by the Reddit API."""

    def __init__(
        self,
        *,
        url: str,
        retry_after: int | None,
        cause: Exception,
    ) -> None:
        """Initialize with retry context and underlying cause."""
        self.url = url
        self.retry_after = retry_after
        self.cause = cause
        message = f"Rate limited by Reddit API for '{self.url}'."
        if self.retry_after is not None:
            message = f"{message} Retry after: {self.retry_after}s."
        super().__init__(message, cause=cause, url=url)


class RedditScraperResponseParseError(RedditScraperProviderError):
    """Raised when a JSON response cannot be parsed."""

    def __init__(self, *, url: str, cause: Exception) -> None:
        """Initialize with URL context and underlying cause."""
        self.url = url
        self.cause = cause
        message = (
            f"Failed to parse JSON response from '{self.url}'. "
            f"Original error: {self.cause}"
        )
        super().__init__(message, cause=cause, url=url)


class RedditScraperUnexpectedResponseError(RedditScraperProviderError):
    """Raised when the response structure is not as expected."""

    def __init__(
        self,
        *,
        url: str,
        reason: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize with URL context and a human-readable reason."""
        self.url = url
        self.reason = reason
        self.cause = cause
        message = f"Unexpected response from '{self.url}': {self.reason}"
        super().__init__(message, cause=cause, url=url)
