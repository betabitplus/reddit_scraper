"""Request execution helpers for reddit_scraper."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from reddit_scraper._internal.components.retry import is_retryable_exception


@dataclass(frozen=True)
class RequestSpec:
    """Settings for a single GET request."""

    client: httpx.Client
    url: str
    params: dict[str, object] | None
    headers: dict[str, str]
    max_retries: int
    before_sleep: Callable[..., object] | None


def perform_get(spec: RequestSpec) -> httpx.Response:
    """Execute a GET request with retry handling."""

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(spec.max_retries),
        retry=retry_if_exception(is_retryable_exception),
        before_sleep=spec.before_sleep,
        reraise=True,
    )
    def _request() -> httpx.Response:
        """Perform one HTTP attempt (wrapped by tenacity)."""
        response = spec.client.get(
            spec.url,
            params=spec.params,
            headers=spec.headers,
        )
        response.raise_for_status()
        return response

    return _request()
