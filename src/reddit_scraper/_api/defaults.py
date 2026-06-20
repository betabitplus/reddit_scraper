"""Built-in default declarations for `reddit_scraper`.

Why:
    Keeps shared configuration defaults and small runtime catalogs in one
    declaration layer instead of scattering literals across config and
    implementation modules.

How:
    Treat these values as source declarations, not mutable runtime state.
    Runtime code is responsible for deriving concrete behavior such as cache
    setup and media extension allow-lists.

Notes:
    These values are consumed by config declarations and private runtime code.
    Raw default constants are intentionally not re-exported from the top-level
    package.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

# ================================================================================
# Network Defaults
# ================================================================================

# Range is ≥ 0.1.
DEFAULT_NETWORK_TIMEOUT_SECONDS: float = 10.0
# Range is ≥ 0.
DEFAULT_NETWORK_MAX_RETRIES: int = 5
# Options are true or false.
DEFAULT_NETWORK_RANDOM_USER_AGENT: bool = True

# ================================================================================
# Cache Defaults
# ================================================================================

# Options are true or false.
DEFAULT_CACHE_ENABLED: bool = True
# Range is ≥ 0.
DEFAULT_CACHE_MAX_SIZE_MB: float = 500.0
# Type is string or null.
DEFAULT_CACHE_DIR: str | None = None
DEFAULT_MEDIA_CACHE_MAX_SIZE_BYTES: int = 209_715_200

# ================================================================================
# Media Transport Defaults
# ================================================================================

DEFAULT_MEDIA_DIRECT_TIMEOUT_SECONDS: float = 60.0
DEFAULT_MEDIA_PROXY_TIMEOUT_SECONDS: float = 30.0

# ================================================================================
# Media Download Defaults
# ================================================================================

MEDIA_TYPE_IMAGE: str = "image"
MEDIA_TYPE_GIF: str = "gif"
MEDIA_TYPE_VIDEO: str = "video"
MEDIA_TYPE_ALL: str = "all"

SUPPORTED_MEDIA_DOWNLOAD_TYPES: tuple[str, ...] = (
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_GIF,
    MEDIA_TYPE_VIDEO,
    MEDIA_TYPE_ALL,
)

# Options are true or false.
DEFAULT_MEDIA_DOWNLOAD_ENABLED: bool = False
# Options are image, gif, video, or all.
DEFAULT_MEDIA_DOWNLOAD_ALLOWED_TYPES: tuple[str, ...] = (MEDIA_TYPE_IMAGE,)
# Range is ≥ 0.
DEFAULT_MEDIA_DOWNLOAD_MAX_FILE_SIZE_MB: float = 5.0
# Range is ≥ 0.
DEFAULT_MEDIA_DOWNLOAD_MAX_DOWNLOADS_PER_POST: int = 1
# Range is ≥ 0.
DEFAULT_MEDIA_DOWNLOAD_MAX_TOTAL_DOWNLOADS: int = 10
# Options are true or false.
DEFAULT_MEDIA_DOWNLOAD_CACHE_MEDIA: bool = True
# Options are true or false.
DEFAULT_MEDIA_DOWNLOAD_DOWNLOAD_THUMBNAILS: bool = False
# Options are true or false.
DEFAULT_MEDIA_DOWNLOAD_SKIP_HEAD: bool = False
# Options are true or false.
DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_SMALL: bool = True
# Options are true or false.
DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_LARGE: bool = False
# Range is ≥ 0.
DEFAULT_MEDIA_DOWNLOAD_PROXY_SIZE_THRESHOLD_MB: float = 2.0
# Type is string or null.
DEFAULT_MEDIA_DOWNLOAD_CACHE_DIR: str | None = None

# ================================================================================
# Media Catalog Defaults
# ================================================================================

MEDIA_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".bmp", ".jpeg", ".jpg", ".png", ".tiff", ".webp"}
)
MEDIA_GIF_EXTENSIONS: frozenset[str] = frozenset({".gif", ".gifv"})
MEDIA_VIDEO_EXTENSIONS: frozenset[str] = frozenset({".mov", ".mp4", ".webm"})
MEDIA_ALL_EXTENSIONS: frozenset[str] = frozenset(
    MEDIA_IMAGE_EXTENSIONS | MEDIA_GIF_EXTENSIONS | MEDIA_VIDEO_EXTENSIONS
)

MEDIA_TYPE_EXTENSIONS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        MEDIA_TYPE_IMAGE: MEDIA_IMAGE_EXTENSIONS,
        MEDIA_TYPE_GIF: MEDIA_GIF_EXTENSIONS,
        MEDIA_TYPE_VIDEO: MEDIA_VIDEO_EXTENSIONS,
        MEDIA_TYPE_ALL: MEDIA_ALL_EXTENSIONS,
    }
)

# ================================================================================
# Rate Limit Defaults
# ================================================================================

# Range is ≥ 0.
DEFAULT_RATE_LIMIT_REQUEST_DELAY_MIN: float = 1.0
# Range is ≥ 0.
DEFAULT_RATE_LIMIT_REQUEST_DELAY_MAX: float = 2.0

# ================================================================================
# Public Operation Defaults
# ================================================================================

# Options are link, post, or sr.
SUPPORTED_SEARCH_TYPES: tuple[str, ...] = ("link", "post", "sr")
# Options are hot, top, new, rising, or best.
SUPPORTED_GLOBAL_CATEGORIES: tuple[str, ...] = ("hot", "top", "new", "rising", "best")
# Options are hot, top, new, userhot, usertop, or usernew.
SUPPORTED_SUBREDDIT_CATEGORIES: tuple[str, ...] = (
    "hot",
    "top",
    "new",
    "userhot",
    "usertop",
    "usernew",
)
# Options are hour, day, week, month, year, or all.
SUPPORTED_TIME_FILTERS: tuple[str, ...] = (
    "hour",
    "day",
    "week",
    "month",
    "year",
    "all",
)
# Options are relevance, hot, top, new, or comments.
SUPPORTED_SUBREDDIT_SORTS: tuple[str, ...] = (
    "relevance",
    "hot",
    "top",
    "new",
    "comments",
)
# Options are GeoFilter enum values normalized to lowercase strings.
SUPPORTED_GEO_FILTERS: tuple[str, ...] = (
    "ar",
    "au",
    "bg",
    "ca",
    "cl",
    "co",
    "cz",
    "de",
    "es",
    "fi",
    "fr",
    "gb",
    "global",
    "gr",
    "hr",
    "hu",
    "ie",
    "in",
    "is",
    "it",
    "jp",
    "mx",
    "my",
    "nz",
    "ph",
    "pl",
    "pr",
    "pt",
    "ro",
    "rs",
    "se",
    "sg",
    "th",
    "tr",
    "tw",
    "us",
    "us_ak",
    "us_al",
    "us_ar",
    "us_az",
    "us_ca",
    "us_co",
    "us_ct",
    "us_dc",
    "us_de",
    "us_fl",
    "us_ga",
    "us_hi",
    "us_ia",
    "us_id",
    "us_il",
    "us_in",
    "us_ks",
    "us_ky",
    "us_la",
    "us_ma",
    "us_md",
    "us_me",
    "us_mi",
    "us_mn",
    "us_mo",
    "us_ms",
    "us_mt",
    "us_nc",
    "us_" + "n" + "d",
    "us_ne",
    "us_nh",
    "us_nj",
    "us_nm",
    "us_nv",
    "us_ny",
    "us_oh",
    "us_ok",
    "us_or",
    "us_pa",
    "us_ri",
    "us_sc",
    "us_sd",
    "us_tn",
    "us_tx",
    "us_ut",
    "us_va",
    "us_vt",
    "us_wa",
    "us_wi",
    "us_wv",
    "us_wy",
)

# Range is 1 through 100.
DEFAULT_SEARCH_LIMIT: int = 10
# Options are link, post, or sr.
DEFAULT_SEARCH_TYPES: tuple[str, ...] = ("link",)

# Range is 1 through 100.
DEFAULT_SUBREDDIT_SEARCH_LIMIT: int = 10
# Options are relevance, hot, top, new, or comments.
DEFAULT_SUBREDDIT_SEARCH_SORT: str = "relevance"
# Options are link, post, or sr.
DEFAULT_SUBREDDIT_SEARCH_TYPES: tuple[str, ...] = DEFAULT_SEARCH_TYPES

# Range is 1 through 100.
DEFAULT_FEED_LIMIT: int = 10
# Options are hot, top, new, rising, or best.
DEFAULT_FEED_CATEGORY: str = "hot"
# Options are hour, day, week, month, year, or all.
DEFAULT_FEED_TIME_FILTER: str = "all"

# Range is 1 through 100.
DEFAULT_POPULAR_FEED_LIMIT: int = 10
# Options are hot, top, new, rising, or best.
DEFAULT_POPULAR_FEED_CATEGORY: str = "hot"
# Options are hour, day, week, month, year, or all.
DEFAULT_POPULAR_FEED_TIME_FILTER: str = "all"
# Type is string or null.
# Options come from SUPPORTED_GEO_FILTERS.
DEFAULT_POPULAR_FEED_GEO_FILTER: str | None = None

# Range is 1 through 100.
DEFAULT_SUBREDDIT_POSTS_LIMIT: int = 10
# Options are hot, top, new, userhot, usertop, or usernew.
DEFAULT_SUBREDDIT_POSTS_CATEGORY: str = "hot"
# Options are hour, day, week, month, year, or all.
DEFAULT_SUBREDDIT_POSTS_TIME_FILTER: str = "all"

# Range is 1 through 100.
DEFAULT_USER_DATA_LIMIT: int = 10
