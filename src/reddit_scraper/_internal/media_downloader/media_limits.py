"""Size/limit enforcement helpers for the media_downloader domain."""

from __future__ import annotations


def threshold_bytes(proxy_size_threshold_mb: float) -> int:
    """Convert the proxy size threshold (MB) to bytes."""
    return int(proxy_size_threshold_mb * 1024 * 1024)


def max_bytes(max_file_size_mb: float) -> int:
    """Convert the max file size (MB) to bytes."""
    return int(max_file_size_mb * 1024 * 1024)


def check_content_length_action(
    content_length: str | None,
    *,
    max_bytes_limit: int,
    threshold_bytes_limit: int,
    use_proxy: bool,
    use_proxy_for_large: bool,
) -> str:
    """Return action based on Content-Length: ok, skip, or abort."""
    if not content_length:
        return "ok"

    size_bytes = int(content_length)
    if size_bytes > max_bytes_limit:
        return "skip"

    if use_proxy and size_bytes > threshold_bytes_limit and not use_proxy_for_large:
        return "abort"

    return "ok"


def should_abort_proxy_stream(
    size_bytes: int,
    *,
    threshold_bytes_limit: int,
    use_proxy: bool,
    use_proxy_for_large: bool,
) -> bool:
    """Return true when a proxy stream should be aborted for size reasons."""
    if not (use_proxy and size_bytes > threshold_bytes_limit):
        return False
    return not use_proxy_for_large
