"""User scraping operations for the reddit_scraper service.

This module is an internal implementation detail.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from py_lib_runtime import get_logger, log_operation_duration

from reddit_scraper._internal.components.parsing import get_listing_items
from reddit_scraper._internal.components.resolver import (
    get_default_reddit_scraper_resolver,
)
from reddit_scraper._internal.components.utils import sleep_jitter

logger = get_logger(__name__)


class UserMixin:
    """Mixin that provides user data scraping."""

    @staticmethod
    def _parse_user_item(item: dict[str, Any]) -> dict[str, Any] | None:
        """Normalize a user listing item into a post/comment dict."""
        kind = item.get("kind")
        item_data = item.get("data", {})
        if kind == "t3":
            post_url = f"https://www.reddit.com{item_data.get('permalink', '')}"
            return {
                "type": "post",
                "title": item_data.get("title", ""),
                "subreddit": item_data.get("subreddit", ""),
                "url": post_url,
                "created_utc": item_data.get("created_utc", ""),
            }
        if kind == "t1":
            comment_url = f"https://www.reddit.com{item_data.get('permalink', '')}"
            return {
                "type": "comment",
                "subreddit": item_data.get("subreddit", ""),
                "body": item_data.get("body", ""),
                "created_utc": item_data.get("created_utc", ""),
                "url": comment_url,
            }
        return None

    def _extract_comments(self, comments: list[object]) -> list[dict[str, Any]]:
        """Extract nested comments from the Reddit API response."""
        logger.info(
            "Extracting comments",
            event_type="reddit.comments.extract.started",
        )
        extracted_comments = []
        for comment in comments:
            if isinstance(comment, dict):
                comment_dict = cast("dict[str, Any]", comment)
            else:
                continue
            if comment_dict.get("kind") == "t1":
                comment_data = cast("dict[str, Any]", comment_dict.get("data", {}))
                extracted_comment = {
                    "author": comment_data.get("author", ""),
                    "body": comment_data.get("body", ""),
                    "score": comment_data.get("score", ""),
                    "replies": [],
                }

                replies = comment_data.get("replies", "")
                if isinstance(replies, dict):
                    extracted_comment["replies"] = self._extract_comments(
                        replies.get("data", {}).get("children", [])
                    )
                extracted_comments.append(extracted_comment)
        logger.info(
            "Successfully extracted comments",
            event_type="reddit.comments.extract.succeeded",
            report={"count": len(extracted_comments)},
        )
        return extracted_comments

    def _collect_user_items(
        self, items: list[dict[str, Any]], remaining: int
    ) -> list[dict[str, Any]]:
        """Collect parsed user items up to the remaining limit."""
        collected: list[dict[str, Any]] = []
        for item in items:
            if remaining <= 0:
                break
            parsed = self._parse_user_item(item)
            if parsed:
                collected.append(parsed)
                remaining -= 1
        return collected

    def scrape_user_data(
        self,
        username: str,
        limit: int | None = None,
        *,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Scrape a user's posts and comments."""
        with log_operation_duration(
            logger,
            event_type="reddit.user.scrape.completed",
            level=logging.INFO,
            correlation_id=correlation_id,
            username=username,
        ):
            resolver = get_default_reddit_scraper_resolver()
            limit = resolver.resolve_user_limit(limit)

            base_url = f"https://www.reddit.com/user/{username}/.json"
            params = {"limit": limit, "after": None}
            all_items: list[dict[str, Any]] = []
            count = 0

            while count < limit:
                data = self._fetch_json_page(
                    base_url,
                    params,
                    cache_first_page=params["after"] is None,
                    context=f"User data for {username}",
                )

                if data is None:
                    break

                items = get_listing_items(data)
                if not items:
                    logger.info(
                        "No more items found for user",
                        event_type="reddit.user.items.exhausted",
                        username=username,
                    )
                    break

                new_items = self._collect_user_items(items, limit - count)
                all_items.extend(new_items)
                count += len(new_items)

                params["after"] = data.get("data", {}).get("after")
                if not params["after"]:
                    break

                sleep_jitter()
                logger.debug(
                    "Sleeping between pagination requests",
                    event_type="reddit.user.pagination.sleep.started",
                    username=username,
                    limit=limit,
                )
            logger.info(
                "Successfully scraped user data",
                event_type="reddit.user.scrape.succeeded",
                username=username,
                report={"count": len(all_items), "limit": limit},
            )
            return all_items
