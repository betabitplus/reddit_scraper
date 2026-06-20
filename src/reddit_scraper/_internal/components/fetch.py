"""Fetch helpers for reddit_scraper."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
from py_lib_runtime import get_logger

from reddit_scraper._api.errors import (
    RedditScraperRateLimitError,
    RedditScraperRequestError,
    RedditScraperResponseParseError,
)
from reddit_scraper._internal.components.retry import get_retry_after
from reddit_scraper._internal.components.utils import (
    STATUS_SERVER_ERROR,
    STATUS_TOO_MANY_REQUESTS,
)

logger = get_logger(__name__)


def get_json_response(
    get_response: Callable[[], httpx.Response],
    *,
    url: str,
    context: str | None = None,
) -> dict[str, Any] | None:
    """Fetch JSON with consistent error mapping."""
    try:
        response = get_response()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Request failed after retries",
            event_type="reddit.request.failed",
            context=context,
            url=url,
            status_code=exc.response.status_code,
            error={"message": str(exc), "type": type(exc).__name__},
        )
        if exc.response.status_code == STATUS_TOO_MANY_REQUESTS:
            raise RedditScraperRateLimitError(
                url=url,
                retry_after=get_retry_after(exc.response),
                cause=exc,
            ) from exc
        if exc.response.status_code < STATUS_SERVER_ERROR:
            return None
        raise RedditScraperRequestError(url=url, cause=exc) from exc
    except httpx.RequestError as exc:
        logger.warning(
            "Request failed after retries",
            event_type="reddit.request.failed",
            context=context,
            url=url,
            error={"message": str(exc), "type": type(exc).__name__},
        )
        raise RedditScraperRequestError(url=url, cause=exc) from exc
    except ValueError as exc:
        logger.warning(
            "Failed to parse JSON response",
            event_type="reddit.response.parse.failed",
            context=context,
            url=url,
            error={"message": str(exc), "type": type(exc).__name__},
        )
        raise RedditScraperResponseParseError(url=url, cause=exc) from exc
