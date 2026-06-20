# %%
"""Reddit user-data scenario: discovered user timeline.

Why:
    Verifies that the public scraper can discover a user from subreddit posts
    and fetch that user's public timeline.

Covers:
    Area: user data
    Behavior: author discovery and user timeline scraping
    Interface: `fetch_subreddit_posts` and `scrape_user_data`

Checks:
    If author discovery finds a user or uses the fallback, then the serialized
    target user is not empty.
    If user data is fetched, then item counts and subreddit evidence match the
    committed snapshot.

Examples:
    Run manually:
        uv run python -m tests.reddit_scraper.e2e.user_data.test_user_data_pipeline

    Run as test:
        pytest tests/reddit_scraper/e2e/user_data/test_user_data_pipeline.py
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
USER_DISCOVERY_SUBREDDIT = "marvelstudios"
USER_DISCOVERY_LIMIT = 3
USER_DISCOVERY_CATEGORY = "hot"
USER_DATA_LIMIT = 5
FALLBACK_USER = "chanma50"


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
        "discovery_subreddit": USER_DISCOVERY_SUBREDDIT,
        "discovery_limit": USER_DISCOVERY_LIMIT,
        "discovery_category": USER_DISCOVERY_CATEGORY,
        "data_limit": USER_DATA_LIMIT,
        "fallback_user": FALLBACK_USER,
        "proxy": None,
        "timeout": CLIENT_TIMEOUT,
    }


def run_pipeline(
    discovery_subreddit: str,
    discovery_limit: int,
    discovery_category: str,
    data_limit: int,
    fallback_user: str,
    proxy: str | None,
    timeout: int,
) -> dict:
    """Run user data scraping pipeline."""
    with reddit_scraper.RedditScraper(
        config=reddit_scraper.ScraperConfig(proxy=proxy, timeout=timeout)
    ) as scraper:
        hot_posts = scraper.fetch_subreddit_posts(
            discovery_subreddit,
            options=reddit_scraper.SubredditPostsOptions(
                limit=discovery_limit,
                category=discovery_category,
            ),
        )

        target_user = None
        if hot_posts:
            for post in hot_posts:
                author = post.get("author")
                if author and author not in ["[deleted]", "AutoModerator"]:
                    target_user = author
                    break

        if not target_user:
            target_user = fallback_user

        user_data = scraper.scrape_user_data(target_user, limit=data_limit)

    return {"target_user": target_user, "user_data": user_data}


def serialize_response(response: dict) -> dict:
    """Serialize response for snapshot comparison."""
    user_data = response.get("user_data") or []
    posts = [item for item in user_data if item.get("type") == "post"]
    comments = [item for item in user_data if item.get("type") == "comment"]
    subreddits = sorted(
        {item.get("subreddit") for item in user_data if item.get("subreddit")}
    )
    return {
        "target_user": response.get("target_user"),
        "total_items": len(user_data),
        "posts": len(posts),
        "comments": len(comments),
        "subreddits": subreddits[:5],
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


def test_user_data_pipeline_hermetic(snapshot: SnapshotAssertion) -> None:
    require_vcr_cassette_or_record_mode(
        test_file=__file__, test_name="test_user_data_pipeline_hermetic"
    )
    inputs = load_inputs()
    response = run_pipeline(**inputs)
    actual = serialize_response(response)
    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the live user-data scraping demo."""
    console.rule("[header]TEST: User Data[/header]")

    proxy = get_proxy()
    inputs = load_inputs()
    inputs["proxy"] = proxy
    response = run_pipeline(**inputs)
    user_data = response.get("user_data") or []
    result_summary = serialize_response(response)
    samples = user_data[:2]

    console.rule("[subheader]Scenario[/subheader]")
    console.print(
        "[info]Pick a user from hot posts (or fallback) "
        "and fetch their timeline.[/info]"
    )

    console.rule("[subheader]Inputs[/subheader]")
    console.print(
        f"[key]Discovery subreddit:[/key] [value]{USER_DISCOVERY_SUBREDDIT}[/value]"
    )
    console.print(f"[key]Discovery limit:[/key] [value]{USER_DISCOVERY_LIMIT}[/value]")
    console.print(
        f"[key]Discovery category:[/key] [value]{USER_DISCOVERY_CATEGORY}[/value]"
    )
    console.print(f"[key]Data limit:[/key] [value]{USER_DATA_LIMIT}[/value]")
    console.print(f"[key]Fallback user:[/key] [value]{FALLBACK_USER}[/value]")
    console.print(f"[key]Proxy:[/key] [value]{'on' if proxy else 'off'}[/value]")

    console.rule("[subheader]Steps[/subheader]")
    console.print("[key]1)[/key] Fetch hot posts to discover an author")
    console.print("[key]2)[/key] Use fallback user if needed")
    console.print("[key]3)[/key] Fetch user posts/comments")

    console.rule("[subheader]Results[/subheader]")
    console.print(
        f"[key]Target user:[/key] [value]{result_summary.get('target_user')}[/value]"
    )
    console.print(
        "[key]Totals:[/key] "
        f"items={result_summary.get('total_items')}, "
        f"posts={result_summary.get('posts')}, "
        f"comments={result_summary.get('comments')}"
    )
    console.print(
        "[key]Subreddits (evidence):[/key] "
        f"[value]{result_summary.get('subreddits')}[/value]"
    )

    console.rule("[subheader]Evidence[/subheader]")
    for item in samples:
        text = item.get("title") or item.get("body") or item.get("content")
        console.print(f"[key]Type:[/key] [value]{item.get('type')}[/value]")
        console.print(f"[key]Subreddit:[/key] [value]{item.get('subreddit')}[/value]")
        console.print(f"[key]Text:[/key] [value]{text}[/value]")
        console.print(
            "[key]Permalink:[/key] "
            f"[value]{item.get('permalink') or item.get('link')}[/value]"
        )


if __name__ == "__main__":
    main()

# %%
