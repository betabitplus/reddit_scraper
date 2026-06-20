"""Retry transport integration tests.

Why:
    Verifies the private retry transport seam with a local deterministic server
    instead of mixing private method calls into e2e scenarios.

Covers:
    Area: retry transport
    Behavior: retryable HTTP failures
    Interface: private scraper transport seam

Checks:
    If a local endpoint fails twice and then succeeds, then the scraper returns
    the successful response after three attempts.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer

from reddit_scraper._internal import RedditScraper, ScraperConfig

# =============================================================================
# Helpers
# =============================================================================


@contextmanager
def flaky_json_server() -> Iterator[tuple[str, dict[str, int]]]:
    """Run a local server that succeeds after two transient failures."""
    attempts = {"count": 0}

    class FlakyHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            """Return two retryable failures, then a JSON success payload."""
            attempts["count"] += 1
            if attempts["count"] <= 2:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"temporary error")
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {"status": "ok", "attempts": attempts["count"]}
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        def log_message(self, message_format: str, *args: object) -> None:
            """Silence stdlib HTTP request logging during tests."""
            _ = message_format, args

    server = HTTPServer(("127.0.0.1", 0), FlakyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/retry-probe", attempts
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


# =============================================================================
# Tests
# =============================================================================


def test_retry_transport_succeeds_after_retryable_failures() -> None:
    """Keep retry behavior stable for transient HTTP failures."""
    with flaky_json_server() as (url, attempts):
        scraper = RedditScraper(config=ScraperConfig(proxy=None, timeout=5))
        try:
            response = scraper._get(url)
        finally:
            scraper.close()

    assert response.status_code == 200
    assert attempts["count"] == 3
