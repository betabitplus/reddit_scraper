"""Retry helpers for reddit_scraper."""

from __future__ import annotations

import httpx

from reddit_scraper._internal.components.utils import (
    STATUS_SERVER_ERROR,
    STATUS_TOO_MANY_REQUESTS,
)


def is_retryable_exception(exc: BaseException) -> bool:
    """Determine if an exception warrants a retry."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == STATUS_TOO_MANY_REQUESTS or status >= STATUS_SERVER_ERROR
    return bool(isinstance(exc, httpx.RequestError | httpx.TimeoutException))


def get_retry_after(response: httpx.Response) -> int | None:
    """Parse retry-after header into seconds, if available."""
    retry_after = response.headers.get("retry-after")
    if not retry_after:
        return None
    try:
        return int(retry_after)
    except ValueError:
        return None
