"""Domain types for the reddit_scraper module.

This module defines reddit-specific domain types:
- Enums for search types, time filters, sort categories, geo filters, media types
- Dataclasses for scraper options and reddit cache entries
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from reddit_scraper._api.defaults import (
    DEFAULT_MEDIA_DOWNLOAD_ALLOWED_TYPES,
    DEFAULT_MEDIA_DOWNLOAD_CACHE_MEDIA,
    DEFAULT_MEDIA_DOWNLOAD_DOWNLOAD_THUMBNAILS,
    DEFAULT_MEDIA_DOWNLOAD_ENABLED,
    DEFAULT_MEDIA_DOWNLOAD_MAX_DOWNLOADS_PER_POST,
    DEFAULT_MEDIA_DOWNLOAD_MAX_FILE_SIZE_MB,
    DEFAULT_MEDIA_DOWNLOAD_MAX_TOTAL_DOWNLOADS,
    DEFAULT_MEDIA_DOWNLOAD_PROXY_SIZE_THRESHOLD_MB,
    DEFAULT_MEDIA_DOWNLOAD_SKIP_HEAD,
    DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_LARGE,
    DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_SMALL,
    MEDIA_ALL_EXTENSIONS,
    MEDIA_TYPE_EXTENSIONS,
    SUPPORTED_MEDIA_DOWNLOAD_TYPES,
)
from reddit_scraper._api.errors import InvalidConfigValueError


class SearchType(StrEnum):
    """Reddit search result types."""

    LINK = "link"  # Posts/links (default)
    POST = "post"  # Alias for LINK
    SR = "sr"  # Subreddits


class TimeFilter(StrEnum):
    """Time filter for Reddit 'top' sorting."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


class SortCategory(StrEnum):
    """Sort category for Reddit posts."""

    HOT = "hot"
    TOP = "top"
    NEW = "new"
    RISING = "rising"
    BEST = "best"


_GEO_FILTER_VALUES = {
    "GLOBAL": "GLOBAL",
    "US": "US",
    "AR": "AR",
    "AU": "AU",
    "BG": "BG",
    "CA": "CA",
    "CL": "CL",
    "CO": "CO",
    "HR": "HR",
    "CZ": "CZ",
    "FI": "FI",
    "FR": "FR",
    "DE": "DE",
    "GR": "GR",
    "HU": "HU",
    "IS": "IS",
    "IN": "IN",
    "IE": "IE",
    "IT": "IT",
    "JP": "JP",
    "MY": "MY",
    "MX": "MX",
    "NZ": "NZ",
    "PH": "PH",
    "PL": "PL",
    "PT": "PT",
    "PR": "PR",
    "RO": "RO",
    "RS": "RS",
    "SG": "SG",
    "ES": "ES",
    "SE": "SE",
    "TW": "TW",
    "TH": "TH",
    "TR": "TR",
    "GB": "GB",
    "US_WA": "US_WA",
    "US_DE": "US_DE",
    "US_DC": "US_DC",
    "US_WI": "US_WI",
    "US_WV": "US_WV",
    "US_HI": "US_HI",
    "US_FL": "US_FL",
    "US_WY": "US_WY",
    "US_NH": "US_NH",
    "US_NJ": "US_NJ",
    "US_NM": "US_NM",
    "US_TX": "US_TX",
    "US_LA": "US_LA",
    "US_NC": "US_NC",
    "US_" + "N" + "D": "US_" + "N" + "D",
    "US_NE": "US_NE",
    "US_TN": "US_TN",
    "US_NY": "US_NY",
    "US_PA": "US_PA",
    "US_CA": "US_CA",
    "US_NV": "US_NV",
    "US_VA": "US_VA",
    "US_CO": "US_CO",
    "US_AK": "US_AK",
    "US_AL": "US_AL",
    "US_AR": "US_AR",
    "US_VT": "US_VT",
    "US_IL": "US_IL",
    "US_GA": "US_GA",
    "US_IN": "US_IN",
    "US_IA": "US_IA",
    "US_OK": "US_OK",
    "US_AZ": "US_AZ",
    "US_ID": "US_ID",
    "US_CT": "US_CT",
    "US_ME": "US_ME",
    "US_MD": "US_MD",
    "US_MA": "US_MA",
    "US_OH": "US_OH",
    "US_UT": "US_UT",
    "US_MO": "US_MO",
    "US_MN": "US_MN",
    "US_MI": "US_MI",
    "US_RI": "US_RI",
    "US_KS": "US_KS",
    "US_MT": "US_MT",
    "US_MS": "US_MS",
    "US_SC": "US_SC",
    "US_KY": "US_KY",
    "US_OR": "US_OR",
    "US_SD": "US_SD",
}

GeoFilter = StrEnum("GeoFilter", _GEO_FILTER_VALUES, module=__name__)
GeoFilter.__doc__ = "Geographic filter for r/popular."


class MediaType(StrEnum):
    """Media types for filtering downloads."""

    IMAGE = "image"
    GIF = "gif"
    VIDEO = "video"
    ALL = "all"


@dataclass(frozen=True)
class ClientOptions:
    """Client configuration for network and cache settings."""

    proxy: str | None = None
    timeout: float | None = None
    cache_dir: str | None = None
    cache_enabled: bool | None = None


@dataclass(frozen=True)
class SearchOptions:
    """Search options for global Reddit search."""

    limit: int | None = None
    after: str | None = None
    before: str | None = None
    search_types: list[str] | None = None


@dataclass(frozen=True)
class SubredditSearchOptions(SearchOptions):
    """Search options for subreddit search."""

    sort: str | None = None


@dataclass(frozen=True)
class FeedOptions:
    """Options for global feed requests."""

    limit: int | None = None
    category: str | None = None
    time_filter: str | None = None


@dataclass(frozen=True)
class PopularFeedOptions(FeedOptions):
    """Options for r/popular feed requests."""

    geo_filter: str | None = None


@dataclass(frozen=True)
class SubredditPostsOptions(FeedOptions):
    """Options for subreddit post listings."""


@dataclass
class RedditCacheEntry:
    """Cached Reddit API response."""

    url: str
    response_data: dict
    timestamp: str | None = None
    metadata: dict = field(default_factory=dict)


# =============================================================================
# Media DTOs
# =============================================================================


class _MediaConfigValidation:
    """Local validators used by media config DTO construction."""

    @staticmethod
    def number(
        *,
        field_name: str,
        value: object,
        minimum: float,
        include_minimum: bool = True,
    ) -> None:
        """Validate numeric media settings before downloader runtime uses them."""
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise InvalidConfigValueError(
                field=field_name,
                value=value,
                reason="must be a number",
            )
        if include_minimum:
            is_too_small = value < minimum
            minimum_reason = f"must be greater than or equal to {minimum:g}"
        else:
            is_too_small = value <= minimum
            minimum_reason = f"must be greater than {minimum:g}"
        if is_too_small:
            raise InvalidConfigValueError(
                field=field_name,
                value=value,
                reason=minimum_reason,
            )

    @staticmethod
    def allowed_types(value: object) -> tuple[str, ...]:
        """Normalize media type lists into an immutable runtime tuple."""
        if isinstance(value, set):
            value = tuple(sorted(value))
        elif isinstance(value, list):
            value = tuple(value)
        if not isinstance(value, tuple):
            raise InvalidConfigValueError(
                field="allowed_types",
                value=value,
                reason="must be a list, set, or tuple of media type strings",
            )
        invalid = [item for item in value if item not in SUPPORTED_MEDIA_DOWNLOAD_TYPES]
        if invalid:
            raise InvalidConfigValueError(
                field="allowed_types",
                value=invalid,
                reason=f"must be one of {list(SUPPORTED_MEDIA_DOWNLOAD_TYPES)}",
            )
        return value


@dataclass(frozen=True, slots=True)
class MediaConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for media downloading."""

    enabled: bool = DEFAULT_MEDIA_DOWNLOAD_ENABLED
    allowed_types: tuple[str, ...] = DEFAULT_MEDIA_DOWNLOAD_ALLOWED_TYPES
    max_file_size_mb: float = DEFAULT_MEDIA_DOWNLOAD_MAX_FILE_SIZE_MB
    max_downloads_per_post: int = DEFAULT_MEDIA_DOWNLOAD_MAX_DOWNLOADS_PER_POST
    max_total_downloads: int = DEFAULT_MEDIA_DOWNLOAD_MAX_TOTAL_DOWNLOADS
    cache_media: bool = DEFAULT_MEDIA_DOWNLOAD_CACHE_MEDIA
    download_thumbnails: bool = DEFAULT_MEDIA_DOWNLOAD_DOWNLOAD_THUMBNAILS
    skip_head: bool = DEFAULT_MEDIA_DOWNLOAD_SKIP_HEAD
    use_proxy_for_small: bool = DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_SMALL
    use_proxy_for_large: bool = DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_LARGE
    proxy_size_threshold_mb: float = DEFAULT_MEDIA_DOWNLOAD_PROXY_SIZE_THRESHOLD_MB

    def __post_init__(self) -> None:
        """Validate media config before downloader setup consumes it."""
        object.__setattr__(
            self,
            "allowed_types",
            _MediaConfigValidation.allowed_types(self.allowed_types),
        )
        _MediaConfigValidation.number(
            field_name="max_file_size_mb",
            value=self.max_file_size_mb,
            minimum=0,
            include_minimum=False,
        )
        _MediaConfigValidation.number(
            field_name="max_downloads_per_post",
            value=self.max_downloads_per_post,
            minimum=0,
        )
        _MediaConfigValidation.number(
            field_name="max_total_downloads",
            value=self.max_total_downloads,
            minimum=0,
        )
        _MediaConfigValidation.number(
            field_name="proxy_size_threshold_mb",
            value=self.proxy_size_threshold_mb,
            minimum=0,
            include_minimum=False,
        )

    def get_allowed_extensions(self) -> set[str]:
        """Get file extensions allowed by the configured media types."""
        if "all" in self.allowed_types:
            return set(MEDIA_ALL_EXTENSIONS)

        extensions: set[str] = set()
        for media_type in self.allowed_types:
            extensions.update(MEDIA_TYPE_EXTENSIONS[media_type])
        return extensions


@dataclass(slots=True)
class MediaItem:
    """Represents a downloaded or cached media item."""

    url: str
    content: bytes
    content_type: str
    extension: str
    size_bytes: int
    from_cache: bool = False
    timestamp: str | None = None


# =============================================================================
# Response Contracts
# =============================================================================


@dataclass
class SearchResponse:
    """Standardized response from Reddit search operations."""

    results: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        """Number of results returned."""
        return len(self.results)


@dataclass
class PostDetailsResponse:
    """Response from post details scraping."""

    title: str
    body: str
    comments: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserDataResponse:
    """Response from user data scraping."""

    items: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        """Number of items returned."""
        return len(self.items)


@dataclass
class MediaDownloadResponse:
    """Response from media download operations."""

    items: list[Any]
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        """Number of items downloaded."""
        return len(self.items)
