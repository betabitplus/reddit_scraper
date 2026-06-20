"""HTTP primitives for media downloads (retry, streaming, size checks)."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from py_lib_runtime import get_logger
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from reddit_scraper._api.errors import InvalidConfigValueError
from reddit_scraper._api.types import MediaConfig, MediaItem
from reddit_scraper._internal.media_downloader.media_limits import (
    check_content_length_action,
    max_bytes,
    should_abort_proxy_stream,
    threshold_bytes,
)
from reddit_scraper._internal.media_downloader.media_routing import (
    get_extension_from_content_type,
    get_extension_from_url,
    is_allowed_type,
)

logger = get_logger(__name__)

RETRY_STATUS_TOO_MANY_REQUESTS = 429
RETRY_STATUS_SERVER_ERROR = 500


@dataclass(frozen=True)
class DownloadLimits:
    """Precomputed byte thresholds for a download attempt."""

    max_bytes_limit: int
    threshold_bytes_limit: int


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of a media download attempt."""

    item: MediaItem | None
    used_proxy: bool
    reason: str  # ok | skip_size | skip_type | abort_proxy | error


def create_proxy_client(*, timeout_seconds: float, proxy: str | None) -> httpx.Client:
    """Create an HTTP client configured for proxy downloads.

    Raises:
        InvalidConfigValueError: If proxy URL is not provided.
    """
    if not proxy:
        raise InvalidConfigValueError(
            field="proxy",
            value=None,
            reason="Explicit proxy URL is required for create_proxy_client",
        )

    return httpx.Client(
        timeout=timeout_seconds,
        follow_redirects=True,
        proxy=proxy,
        trust_env=False,  # Enforce explicit proxy usage
    )


def create_direct_client(*, timeout_seconds: float) -> httpx.Client:
    """Create an HTTP client configured for direct downloads."""
    return httpx.Client(
        timeout=timeout_seconds,
        follow_redirects=True,
        trust_env=False,  # Enforce explicit proxy usage
    )


def is_retryable(exc: BaseException) -> bool:
    """Return true if an exception is safe to retry."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return (
            status == RETRY_STATUS_TOO_MANY_REQUESTS
            or status >= RETRY_STATUS_SERVER_ERROR
        )
    return isinstance(exc, httpx.RequestError | httpx.TimeoutException)


def log_retry(retry_state: RetryCallState) -> None:
    """Tenacity callback for structured retry logging."""
    sleep_time = retry_state.next_action.sleep if retry_state.next_action else 0
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    error = (
        {"message": str(exc), "type": type(exc).__name__}
        if exc
        else {"message": "Unknown retry reason", "type": "UnknownError"}
    )
    logger.warning(
        "Media download retry",
        event_type="reddit_scraper.media.retry",
        sleep_time=sleep_time,
        attempt_number=retry_state.attempt_number,
        error=error,
    )


def estimate_size_mb(
    url: str,
    *,
    head_client: httpx.Client,
) -> float | None:
    """Estimate content size using a HEAD request (best-effort)."""
    try:
        head_response = head_client.head(url, follow_redirects=True)
        content_length = head_response.headers.get("content-length")
        if content_length:
            return int(content_length) / (1024 * 1024)
    except Exception as exc:  # Defensive: HEAD can fail silently.
        logger.debug(
            "HEAD request failed",
            event_type="reddit_scraper.media.head.failed",
            url=url,
            error={"message": str(exc), "type": type(exc).__name__},
            exc_info=exc,
        )
    return None


def _none_result(*, use_proxy: bool, reason: str) -> DownloadResult:
    """Build a `DownloadResult` for a non-successful outcome."""
    return DownloadResult(item=None, used_proxy=use_proxy, reason=reason)


def _stream_body(
    response: httpx.Response,
    *,
    max_bytes_limit: int,
    threshold_bytes_limit: int,
    use_proxy: bool,
    use_proxy_for_large: bool,
) -> tuple[bytes | None, int, str]:
    """Stream response bytes with size thresholds and proxy-abort logic."""
    stream_url = str(response.request.url)
    chunks: list[bytes] = []
    size_bytes = 0
    for chunk in response.iter_bytes():
        if not chunk:
            continue

        size_bytes += len(chunk)
        if size_bytes > max_bytes_limit:
            logger.debug(
                "Skipping media (too large)",
                event_type="reddit_scraper.media.skip.size",
                url=stream_url,
                size_mb=size_bytes / (1024 * 1024),
                max_size_mb=max_bytes_limit / (1024 * 1024),
            )
            return None, size_bytes, "skip_size"

        if should_abort_proxy_stream(
            size_bytes,
            threshold_bytes_limit=threshold_bytes_limit,
            use_proxy=use_proxy,
            use_proxy_for_large=use_proxy_for_large,
        ):
            logger.info(
                "Aborting proxy download (stream exceeded threshold)",
                event_type="reddit_scraper.media.abort.proxy",
                url=stream_url,
                size_mb=size_bytes / (1024 * 1024),
                proxy_threshold_mb=threshold_bytes_limit / (1024 * 1024),
            )
            return None, size_bytes, "abort_proxy"

        chunks.append(chunk)

    return b"".join(chunks), size_bytes, "ok"


def _validate_content_type(
    url: str,
    *,
    content_type: str,
    config: MediaConfig,
) -> str:
    """Return a reason string based on Content-Type allowlist checks."""
    if is_allowed_type(url, content_type=content_type, config=config):
        return "ok"

    logger.debug(
        "Skipping media (content-type not allowed)",
        event_type="reddit_scraper.media.skip.content_type",
        url=url,
        content_type=content_type,
    )
    return "skip_type"


def _content_length_reason(
    response: httpx.Response,
    *,
    url: str,
    use_proxy: bool,
    limits: DownloadLimits,
    config: MediaConfig,
) -> str:
    """Return a reason string based on Content-Length checks."""
    content_length = response.headers.get("content-length")
    action = check_content_length_action(
        content_length,
        max_bytes_limit=limits.max_bytes_limit,
        threshold_bytes_limit=limits.threshold_bytes_limit,
        use_proxy=use_proxy,
        use_proxy_for_large=config.use_proxy_for_large,
    )

    if action == "skip":
        logger.debug(
            "Skipping media (too large)",
            event_type="reddit_scraper.media.skip.size",
            url=url,
            size_mb=(int(content_length) / (1024 * 1024)) if content_length else None,
            max_size_mb=config.max_file_size_mb,
        )
        return "skip_size"

    if action == "abort":
        logger.info(
            "Aborting proxy download (size exceeds threshold)",
            event_type="reddit_scraper.media.abort.proxy",
            url=url,
            size_mb=(int(content_length) / (1024 * 1024)) if content_length else None,
            proxy_threshold_mb=config.proxy_size_threshold_mb,
        )
        return "abort_proxy"

    return "ok"


def _build_media_item(
    *,
    url: str,
    content: bytes,
    content_type: str,
    size_bytes: int,
) -> MediaItem:
    """Construct a `MediaItem` with an inferred file extension."""
    extension = (
        get_extension_from_url(url)
        or get_extension_from_content_type(content_type)
        or ".bin"
    )
    return MediaItem(
        url=url,
        content=content,
        content_type=content_type,
        extension=extension,
        size_bytes=size_bytes,
        from_cache=False,
        timestamp=None,
    )


def _download_from_response(
    response: httpx.Response,
    *,
    url: str,
    config: MediaConfig,
    use_proxy: bool,
    limits: DownloadLimits,
) -> tuple[MediaItem | None, str]:
    """Download content from an already-open response, returning (item, reason)."""
    content_type = response.headers.get("content-type", "")
    reason = _validate_content_type(url, content_type=content_type, config=config)
    if reason != "ok":
        return None, reason

    reason = _content_length_reason(
        response,
        url=url,
        use_proxy=use_proxy,
        limits=limits,
        config=config,
    )
    if reason != "ok":
        return None, reason

    content, size_bytes, reason = _stream_body(
        response,
        max_bytes_limit=limits.max_bytes_limit,
        threshold_bytes_limit=limits.threshold_bytes_limit,
        use_proxy=use_proxy,
        use_proxy_for_large=config.use_proxy_for_large,
    )
    if reason != "ok" or content is None:
        return None, reason

    if use_proxy and size_bytes > limits.threshold_bytes_limit:
        logger.warning(
            "Proxy download exceeded threshold",
            event_type="reddit_scraper.media.proxy.threshold_exceeded",
            url=url,
            size_mb=size_bytes / (1024 * 1024),
            proxy_threshold_mb=config.proxy_size_threshold_mb,
        )

    return (
        _build_media_item(
            url=url,
            content=content,
            content_type=content_type,
            size_bytes=size_bytes,
        ),
        "ok",
    )


def streaming_download(
    url: str,
    *,
    client: httpx.Client,
    config: MediaConfig,
    use_proxy: bool,
) -> DownloadResult:
    """Download a URL to memory with size/type checks and retries."""
    limits = DownloadLimits(
        max_bytes_limit=max_bytes(config.max_file_size_mb),
        threshold_bytes_limit=threshold_bytes(config.proxy_size_threshold_mb),
    )

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_retryable),
        before_sleep=log_retry,
        reraise=True,
    )
    def _fetch() -> httpx.Response:
        """Perform the streaming GET request (wrapped by tenacity)."""
        request = client.build_request("GET", url)
        return client.send(request, stream=True)

    try:
        response = _fetch()
        response.raise_for_status()
    except Exception as exc:  # Defensive: upstream failures or timeouts.
        logger.warning(
            "Download failed",
            event_type="reddit_scraper.media.download.failed",
            url=url,
            error={"message": str(exc), "type": type(exc).__name__},
            exc_info=exc,
        )
        return _none_result(use_proxy=use_proxy, reason="error")

    try:
        item, reason = _download_from_response(
            response,
            url=url,
            config=config,
            use_proxy=use_proxy,
            limits=limits,
        )
        return DownloadResult(item=item, used_proxy=use_proxy, reason=reason)
    finally:
        response.close()
