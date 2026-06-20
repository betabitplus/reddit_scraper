# %%
"""Reddit feeds scenario: popular geo filters.

Why:
    Verifies that r/popular accepts geographic filters through the public feed
    options and returns normalized listings.

Covers:
    Area: feeds
    Behavior: geo-filtered popular listings
    Interface: `reddit_scraper.RedditScraper.fetch_popular`

Checks:
    If geo-filtered popular feeds replay successfully, then each region count
    and sample subreddit shape matches the committed snapshot.
    If multiple geo filters are used, then overlap evidence remains explicit in
    the serialized response.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.feeds.test_geo_filters_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/feeds/test_geo_filters_pipeline.py
"""

from __future__ import annotations

import os

import pytest
from py_lib_tooling import (
    console,
    require_vcr_cassette_or_record_mode,
)
from syrupy.assertion import SnapshotAssertion

import reddit_scraper

pytestmark = [
    pytest.mark.hermetic,
    pytest.mark.vcr,
]

# =============================================================================
# Scenario
# =============================================================================
CLIENT_TIMEOUT = 15
POPULAR_LIMIT = 5
POPULAR_CATEGORY = "hot"
GEO_FILTER_1 = "us"
GEO_FILTER_2 = "au"
GEO_FILTER_3 = "ru"


# =============================================================================
# Helpers
# =============================================================================


def get_proxy() -> str | None:
    """Get proxy from environment variable (demo-only)."""
    return os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


# =============================================================================
# Pipeline
# =============================================================================


def load_inputs() -> dict:
    """Load inputs for the pipeline."""
    return {
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(proxy: str | None, timeout: int) -> dict:
    """Run geo filter pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        us_posts = scraper.fetch_popular(
            options=reddit_scraper.PopularFeedOptions(
                limit=POPULAR_LIMIT,
                category=POPULAR_CATEGORY,
                geo_filter=GEO_FILTER_1,
            )
        )
        au_posts = scraper.fetch_popular(
            options=reddit_scraper.PopularFeedOptions(
                limit=POPULAR_LIMIT,
                category=POPULAR_CATEGORY,
                geo_filter=GEO_FILTER_2,
            )
        )
        ru_posts = scraper.fetch_popular(
            options=reddit_scraper.PopularFeedOptions(
                limit=POPULAR_LIMIT,
                category=POPULAR_CATEGORY,
                geo_filter=GEO_FILTER_3,
            )
        )

    return {"us_posts": us_posts, "au_posts": au_posts, "ru_posts": ru_posts}


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    us_posts = response.get("us_posts") or []
    au_posts = response.get("au_posts") or []
    ru_posts = response.get("ru_posts") or []
    us_subs = {p.get("subreddit") for p in us_posts}
    au_subs = {p.get("subreddit") for p in au_posts}
    ru_subs = {p.get("subreddit") for p in ru_posts}
    return {
        "us_count": len(us_posts),
        "au_count": len(au_posts),
        "ru_count": len(ru_posts),
        "overlap_us_au": sorted(us_subs & au_subs)[:5],
        "overlap_us_ru": sorted(us_subs & ru_subs)[:5],
        "overlap_au_ru": sorted(au_subs & ru_subs)[:5],
        "unique_us": sorted(us_subs - au_subs - ru_subs)[:5],
        "unique_au": sorted(au_subs - us_subs - ru_subs)[:5],
        "unique_ru": sorted(ru_subs - us_subs - au_subs)[:5],
    }


# =============================================================================
# Assertions
# =============================================================================


def assert_pipeline_response(actual: object, snapshot: SnapshotAssertion) -> None:
    """Verify the serialized response matches the committed scenario snapshot."""
    assert actual == snapshot


# =============================================================================
# Tests
# =============================================================================


def test_geo_filters_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_geo_filters_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live geo-filtered popular feeds demo."""
    console.rule("[header]TEST: Geographic Filters[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    us_posts = response.get("us_posts") or []
    au_posts = response.get("au_posts") or []
    ru_posts = response.get("ru_posts") or []
    result_summary = serialize_response(response)
    us_sample = us_posts[0] if us_posts else {}
    au_sample = au_posts[0] if au_posts else {}
    ru_sample = ru_posts[0] if ru_posts else {}
    regions_differ = any(
        result_summary.get(key) for key in ["unique_us", "unique_au", "unique_ru"]
    )

    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Compare popular feeds by geo filter "
        "to confirm regional differences.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(
        "[key]Geo filters:[/key] "
        f"[value]{GEO_FILTER_1}, {GEO_FILTER_2}, {GEO_FILTER_3}[/value]"
    )
    console.print(f"[key]Limit:[/key] [value]{POPULAR_LIMIT}[/value]")
    console.print(f"[key]Category:[/key] [value]{POPULAR_CATEGORY}[/value]")
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Fetch popular feed with geo=US")
    console.print("[key]2)[/key] Fetch popular feed with geo=AU")
    console.print("[key]3)[/key] Fetch popular feed with geo=RU")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        "[key]Counts:[/key] "
        f"US={result_summary.get('us_count')}, "
        f"AU={result_summary.get('au_count')}, "
        f"RU={result_summary.get('ru_count')}"
    )
    console.print(
        "[key]Overlap US↔AU:[/key] "
        f"[value]{result_summary.get('overlap_us_au')}[/value]"
    )
    console.print(
        "[key]Overlap US↔RU:[/key] "
        f"[value]{result_summary.get('overlap_us_ru')}[/value]"
    )
    console.print(
        "[key]Overlap AU↔RU:[/key] "
        f"[value]{result_summary.get('overlap_au_ru')}[/value]"
    )
    console.print(
        f"[key]Unique US:[/key] [value]{result_summary.get('unique_us')}[/value]"
    )
    console.print(
        f"[key]Unique AU:[/key] [value]{result_summary.get('unique_au')}[/value]"
    )
    console.print(
        f"[key]Unique RU:[/key] [value]{result_summary.get('unique_ru')}[/value]"
    )
    console.print(
        f"[key]Regions differ:[/key] [value]{'yes' if regions_differ else 'no'}[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    console.print("[info]US sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{us_sample.get('title')}[/value]")
    console.print(f"[key]Subreddit:[/key] [value]{us_sample.get('subreddit')}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{us_sample.get('permalink') or us_sample.get('link')}[/value]"
    )
    console.print("[info]AU sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{au_sample.get('title')}[/value]")
    console.print(f"[key]Subreddit:[/key] [value]{au_sample.get('subreddit')}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{au_sample.get('permalink') or au_sample.get('link')}[/value]"
    )
    console.print("[info]RU sample:[/info]")
    console.print(f"[key]Title:[/key] [value]{ru_sample.get('title')}[/value]")
    console.print(f"[key]Subreddit:[/key] [value]{ru_sample.get('subreddit')}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{ru_sample.get('permalink') or ru_sample.get('link')}[/value]"
    )


if __name__ == "__main__":
    main()

# %%
