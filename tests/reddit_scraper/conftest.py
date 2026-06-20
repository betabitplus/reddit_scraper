"""Package-specific pytest fixtures for Reddit scraper tests.

Why:
    Keeps Reddit replay, snapshot, and cache-isolation policy under the
    package test tree while root pytest setup remains product-agnostic.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from py_lib_tooling import method_case_insensitive
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension

FILTER_HEADERS = [
    "api-key",
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-goog-api-key",
]
MATCH_ON = ["method", "scheme", "host", "port", "path", "body"]
VOLATILE_RESPONSE_HEADERS = [
    "Age",
    "CF-RAY",
    "Connection",
    "Date",
    "Server",
    "Transfer-Encoding",
    "cf-cache-status",
]


def pytest_recording_configure(config: pytest.Config, vcr: Any) -> None:
    """Configure pytest-recording's VCR instance for Reddit tests."""
    _ = config
    vcr.register_matcher("method", method_case_insensitive)


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    """Configure VCR for hermetic Reddit HTTP replay."""
    return {
        "filter_headers": FILTER_HEADERS,
        "match_on": MATCH_ON,
        "allow_playback_repeats": False,
        "decode_compressed_response": True,
        "before_record_response": _vcr_scrub_response,
    }


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Use JSON snapshots for readable e2e evidence."""
    return snapshot.use_extension(JSONSnapshotExtension)


@pytest.fixture(autouse=True)
def clear_all_caches_after_test() -> Generator[None]:
    """Clear singleton service caches after each test."""
    yield

    from reddit_scraper._internal.scraper.service import (
        close_default_reddit_scraper_service,
    )

    close_default_reddit_scraper_service()


def _vcr_scrub_response(response: Any) -> Any:
    """Remove volatile response headers from Reddit cassettes."""
    if not isinstance(response, dict):
        return response

    headers = response.get("headers")
    if not isinstance(headers, dict):
        return response

    for header_name in VOLATILE_RESPONSE_HEADERS:
        headers.pop(header_name, None)
        headers.pop(header_name.lower(), None)
    return response
