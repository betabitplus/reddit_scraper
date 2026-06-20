"""HTTP client helpers for reddit_scraper."""

from __future__ import annotations

import httpx
from fake_useragent import UserAgent


def create_user_agent(*, enabled: bool) -> UserAgent | None:
    """Create a random user-agent provider when enabled."""
    return UserAgent() if enabled else None


def build_headers(user_agent: UserAgent | None) -> dict[str, str]:
    """Build request headers for Reddit requests."""
    if user_agent:
        return {"User-Agent": user_agent.random}
    return {}


def create_http_client(
    *,
    timeout: float,
    max_retries: int,
    proxy: str | None,
) -> httpx.Client:
    """Create a configured HTTP client."""
    transport = httpx.HTTPTransport(retries=max_retries)
    return httpx.Client(
        transport=transport,
        timeout=timeout,
        follow_redirects=True,
        proxy=proxy,
        trust_env=False,  # Enforce explicit proxy usage
    )
