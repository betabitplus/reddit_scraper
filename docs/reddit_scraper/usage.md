---
name: reddit-scraper-usage
doc_type: usage
description: Representative public usage patterns for Reddit scraper. Use when you need examples of common caller workflows.
---

# Usage

## Overview

This document shows representative caller workflows through the supported
`reddit_scraper` root package.

## Examples

## 1. Pattern: Search Reddit

Use when:
The caller needs a global Reddit query with typed search options.

```python
import reddit_scraper

response = reddit_scraper.search_reddit(
    "python",
    options=reddit_scraper.SearchOptions(limit=5),
)
print(response.count)
```

## 2. Pattern: Fetch A Subreddit

Use when:
The caller needs posts from one named subreddit with listing options.

```python
import reddit_scraper

posts = reddit_scraper.fetch_subreddit_posts(
    "python",
    options=reddit_scraper.SubredditPostsOptions(limit=10, category="hot"),
)
```

## 3. Pattern: Advanced Client

Use when:
The caller needs an explicit scraper lifecycle with custom timeout or cache
settings.

```python
import reddit_scraper

with reddit_scraper.RedditScraper(
    config=reddit_scraper.ScraperConfig(timeout=15, cache_enabled=True),
) as scraper:
    results = scraper.search_reddit(
        "python",
        options=reddit_scraper.SearchOptions(limit=5),
    )
```

## 4. Pattern: Media Download

Use when:
The caller needs to enable media download settings for one direct media URL.

```python
from dataclasses import replace

import reddit_scraper

config = replace(reddit_scraper.get_default_media_config(), enabled=True)
result = reddit_scraper.download_media(
    "https://picsum.photos/seed/cache/200/300.jpg",
    config=config,
)
```
