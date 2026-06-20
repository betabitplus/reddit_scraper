---
name: reddit-scraper-workbench-verification
doc_type: verification
description: Manual workbench verification for Reddit scraper. Use when you need the live isolated feature probe story.
---

# Workbench Verification

## Overview

This document describes the manual live workbench probes that mirror the e2e
feature slices without importing the shipped `reddit_scraper` package or its
private runtime modules.

## Proof Areas

## 1. Proof: Search

These probes show that global search and result-type filtering work directly
against Reddit JSON.

### Seen In Scripts

- [global_query.py](../../../workbench/reddit_scraper/search/global_query.py)
- [search_type_filtering.py](../../../workbench/reddit_scraper/search/search_type_filtering.py)

## 2. Proof: Feeds

These probes show that global feed families, time filters, geo filters, and
pagination each have isolated live evidence.

### Seen In Scripts

- [global_families.py](../../../workbench/reddit_scraper/feeds/global_families.py)
- [time_filter.py](../../../workbench/reddit_scraper/feeds/time_filter.py)
- [after_pagination.py](../../../workbench/reddit_scraper/feeds/after_pagination.py)
- [search_after_pagination.py](../../../workbench/reddit_scraper/feeds/search_after_pagination.py)
- [geo_filters.py](../../../workbench/reddit_scraper/feeds/geo_filters.py)

## 3. Proof: Subreddit Posts

This probe shows subreddit-scoped search and hot listing evidence.

### Seen In Scripts

- [scoped_search_and_listing.py](../../../workbench/reddit_scraper/subreddit_posts/scoped_search_and_listing.py)

## 4. Proof: Post Details

This probe shows permalink discovery and nested comment extraction.

### Seen In Scripts

- [comment_extraction.py](../../../workbench/reddit_scraper/post_details/comment_extraction.py)

## 5. Proof: User Data

This probe shows author discovery and public user timeline extraction.

### Seen In Scripts

- [discovered_timeline.py](../../../workbench/reddit_scraper/user_data/discovered_timeline.py)

## 6. Proof: Cache

This probe shows API response cache population and reuse for repeated
equivalent search requests.

### Seen In Scripts

- [repeated_search_reuse.py](../../../workbench/reddit_scraper/cache/repeated_search_reuse.py)

## 7. Proof: Provider Degradation

This probe shows invalid-subreddit degradation as public empty-result evidence.

### Seen In Scripts

- [invalid_subreddit_empty.py](../../../workbench/reddit_scraper/retry/invalid_subreddit_empty.py)

## 8. Proof: Media

These probes show image discovery, proxy abort/direct retry for a discovered
Reddit image, and discovered-image on-demand download cache reuse.

### Seen In Scripts

- [image_post_discovery.py](../../../workbench/reddit_scraper/media/image_post_discovery.py)
- [proxy_abort_direct_retry.py](../../../workbench/reddit_scraper/media/proxy_abort_direct_retry.py)
- [on_demand_discovered_image.py](../../../workbench/reddit_scraper/media/on_demand_discovered_image.py)

## Rules

- Keep workbench manual-only and live-first.
- Do not import the shipped `reddit_scraper` package from workbench scripts.
- Keep one workbench script focused on one behavior or tightly related concept.
- Use workbench to document dependency behavior before or while it remains
  product behavior.
