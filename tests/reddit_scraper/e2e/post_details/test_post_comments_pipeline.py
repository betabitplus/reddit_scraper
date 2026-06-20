# %%
"""Reddit post-details scenario: comment extraction.

Why:
    Verifies that the public scraper can locate a post permalink and fetch the
    corresponding title and nested comments.

Covers:
    Area: post details
    Behavior: post permalink resolution and comment extraction
    Interface: `search_reddit`, `fetch_subreddit_posts`, and `scrape_post_details`

Checks:
    If a permalink is found, then post-detail evidence matches the committed
    snapshot.
    If comments are returned, then recursive comment counting and top-author
    evidence stay serialized.

Examples:
    Run manually:
        uv run python -m \
            tests.reddit_scraper.e2e.post_details.test_post_comments_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/post_details/test_post_comments_pipeline.py
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
SEARCH_QUERY = "Avengers Doomsday trailer"
SEARCH_LIMIT = 1

FALLBACK_SUBREDDIT = "marvelstudios"
FALLBACK_CATEGORY = "hot"
FALLBACK_LIMIT = 1


# =============================================================================
# Helpers
# =============================================================================


def get_proxy() -> str | None:
    """Get proxy from environment variable (demo-only)."""
    return os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


def count_comments(comments: list[dict]) -> int:
    """Recursively count comments and replies."""
    total = 0
    for comment in comments:
        total += 1
        if comment.get("replies"):
            total += count_comments(comment["replies"])
    return total


# =============================================================================
# Pipeline
# =============================================================================


def load_inputs() -> dict:
    """Load inputs for the pipeline."""
    return {
        "search_query": SEARCH_QUERY,
        "search_limit": SEARCH_LIMIT,
        "fallback_subreddit": FALLBACK_SUBREDDIT,
        "fallback_category": FALLBACK_CATEGORY,
        "fallback_limit": FALLBACK_LIMIT,
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(
    search_query: str,
    search_limit: int,
    fallback_subreddit: str,
    fallback_category: str,
    fallback_limit: int,
    proxy: str | None,
    timeout: int,
) -> dict:
    """Run post comment scraping pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        search_results = scraper.search_reddit(
            search_query,
            options=reddit_scraper.SearchOptions(limit=search_limit),
        )

        permalink = None
        if not search_results:
            fallback_posts = scraper.fetch_subreddit_posts(
                fallback_subreddit,
                options=reddit_scraper.SubredditPostsOptions(
                    limit=fallback_limit,
                    category=fallback_category,
                ),
            )
            if fallback_posts:
                permalink = fallback_posts[0].get("permalink")
        else:
            link = search_results[0].get("link", "")
            if link:
                permalink = link.replace("https://www.reddit.com", "")

        if not permalink:
            return {"found": False}

        post_details = scraper.scrape_post_details(permalink)
        return {
            "found": post_details is not None,
            "permalink": permalink,
            "post_details": post_details,
        }


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    if not response.get("found"):
        return {"found": False}

    post_details = response["post_details"] or {}
    comments = post_details.get("comments", [])
    return {
        "found": True,
        "permalink": response.get("permalink"),
        "title_length": len(post_details.get("title", "")),
        "comment_count": count_comments(comments),
        "top_authors": [c.get("author") for c in comments[:3] if c.get("author")],
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


def test_post_comments_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_post_comments_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live post-comments demo."""
    console.rule("[header]TEST: Post Comments[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    result_summary = serialize_response(response)
    post_title = (response.get("post_details") or {}).get("title")
    comments = (response.get("post_details") or {}).get("comments", [])

    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Find a post (search or fallback) and extract its comments.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(f"[key]Search query:[/key] [value]{SEARCH_QUERY}[/value]")
    console.print(f"[key]Search limit:[/key] [value]{SEARCH_LIMIT}[/value]")
    console.print(
        "[key]Fallback:[/key] "
        f"[value]r/{FALLBACK_SUBREDDIT}, {FALLBACK_CATEGORY}, "
        f"limit={FALLBACK_LIMIT}[/value]"
    )
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Search for a post")
    console.print("[key]2)[/key] If missing, use fallback subreddit post")
    console.print("[key]3)[/key] Fetch post details and comments")

    console.rule("[subheader]Results[/subheader]")
    console.print(f"[key]Found:[/key] [value]{result_summary.get('found')}[/value]")
    console.print(
        "[key]Comment count:[/key] "
        f"[value]{result_summary.get('comment_count')}[/value]"
    )
    console.print(
        f"[key]Top authors:[/key] [value]{result_summary.get('top_authors')}[/value]"
    )

    console.rule("[subheader]Examples[/subheader]")
    console.print(f"[key]Permalink:[/key] [value]{response.get('permalink')}[/value]")
    console.print(f"[key]Title:[/key] [value]{post_title}[/value]")
    if comments:
        console.print("[info]Top 5 comment threads (raw JSON):[/info]")
        console.print_json({"threads": comments[:5]})


if __name__ == "__main__":
    main()

# %%
