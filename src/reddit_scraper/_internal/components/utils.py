"""Utility helpers for the reddit_scraper package."""

from __future__ import annotations

import secrets
import time

from reddit_scraper._internal.config import get_reddit_scraper_config

STATUS_TOO_MANY_REQUESTS = 429
STATUS_SERVER_ERROR = 500
MAX_PAGE_SIZE = 100
MIN_POST_DETAIL_BLOCKS = 2


def sleep_jitter(
    min_seconds: float | None = None,
    max_seconds: float | None = None,
) -> None:
    """Sleep for a small jitter window to avoid rate limits."""
    if min_seconds is None or max_seconds is None:
        defaults = get_reddit_scraper_config().rate_limit
        min_seconds = defaults.request_delay_min
        max_seconds = defaults.request_delay_max
    if max_seconds < min_seconds:
        min_seconds, max_seconds = max_seconds, min_seconds
    span = max_seconds - min_seconds
    if span <= 0:
        time.sleep(min_seconds)
        return
    milliseconds = int(span * 1000)
    time.sleep(min_seconds + (secrets.randbelow(milliseconds + 1) / 1000))
