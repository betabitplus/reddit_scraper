# %%
"""Reddit media scenario: image post discovery.

Why:
    Verifies that public subreddit listings expose image or thumbnail evidence
    for media-oriented posts.

Covers:
    Area: media
    Behavior: image URL discovery from subreddit listings
    Interface: `reddit_scraper.RedditScraper.fetch_subreddit_posts`

Checks:
    If image posts are discovered through the primary or fallback subreddit,
    then the serialized count and sample URLs match the committed snapshot.
    If a sample is shown manually, then it includes an image or thumbnail URL.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.media.test_image_posts_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/media/test_image_posts_pipeline.py
"""

from __future__ import annotations

import os

import pytest
from IPython.display import Markdown, display
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
PRIMARY_SUBREDDIT = "marvelstudios"
FALLBACK_SUBREDDIT = "Marvel"
POSTS_LIMIT = 10
POSTS_CATEGORY = "hot"
MAX_IMAGES = 2


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
        "primary_subreddit": PRIMARY_SUBREDDIT,
        "fallback_subreddit": FALLBACK_SUBREDDIT,
        "posts_limit": POSTS_LIMIT,
        "posts_category": POSTS_CATEGORY,
        "max_images": MAX_IMAGES,
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(
    primary_subreddit: str,
    fallback_subreddit: str,
    posts_limit: int,
    posts_category: str,
    max_images: int,
    proxy: str | None,
    timeout: int,
) -> dict:
    """Run image discovery pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        posts = scraper.fetch_subreddit_posts(
            primary_subreddit,
            options=reddit_scraper.SubredditPostsOptions(
                limit=posts_limit,
                category=posts_category,
            ),
        )

        image_posts = [
            p for p in posts if p.get("image_url") or p.get("thumbnail_url")
        ][:max_images]

        if not image_posts:
            posts = scraper.fetch_subreddit_posts(
                fallback_subreddit,
                options=reddit_scraper.SubredditPostsOptions(
                    limit=posts_limit,
                    category=posts_category,
                ),
            )
            image_posts = [
                p for p in posts if p.get("image_url") or p.get("thumbnail_url")
            ][:max_images]

    return {"image_posts": image_posts}


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    image_posts = response.get("image_posts") or []
    return {
        "image_count": len(image_posts),
        "sample_urls": [
            p.get("image_url") or p.get("thumbnail_url") for p in image_posts
        ],
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


def test_image_posts_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_image_posts_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live image-post discovery demo."""
    console.rule("[header]TEST: Image Posts[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    image_posts = response.get("image_posts") or []
    sample = image_posts[0] if image_posts else {}
    image_url = sample.get("image_url") or sample.get("thumbnail_url")
    result_summary = serialize_response(response)
    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Discover image posts using a primary subreddit with a fallback.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Primary subreddit:[/key] [value]{PRIMARY_SUBREDDIT}[/value]")
    console.print(f"[key]Fallback subreddit:[/key] [value]{FALLBACK_SUBREDDIT}[/value]")
    console.print(f"[key]Limit:[/key] [value]{POSTS_LIMIT}[/value]")
    console.print(f"[key]Category:[/key] [value]{POSTS_CATEGORY}[/value]")
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Fetch posts from primary subreddit")
    console.print("[key]2)[/key] Filter posts with image/thumbnail URLs")
    console.print("[key]3)[/key] If none, repeat with fallback subreddit")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        f"[key]Images found:[/key] [value]{result_summary.get('image_count')}[/value]"
    )
    console.print(
        f"[key]Sample URLs:[/key] [value]{result_summary.get('sample_urls')}[/value]"
    )
    console.print(
        "[key]Sample has image URL:[/key] "
        f"[value]{'yes' if image_url else 'no'}[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    console.print(f"[key]Title:[/key] [value]{sample.get('title')}[/value]")
    console.print(f"[key]Image URL:[/key] [value]{image_url}[/value]")
    console.print(
        "[key]Permalink:[/key] "
        f"[value]{sample.get('permalink') or sample.get('link')}[/value]"
    )
    if image_url:
        alt_text = sample.get("title") or "image"
        display(Markdown(f"![{alt_text}]({image_url})"))


if __name__ == "__main__":
    main()

# %%
