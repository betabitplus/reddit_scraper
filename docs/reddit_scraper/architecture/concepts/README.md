---
name: reddit-scraper-concepts
doc_type: index
description: Index of Reddit scraper architecture concepts. Use when you need the concept doc that matches a supported behavior slice.
---

# Concepts

## Overview

These docs describe Reddit scraper behavior slices. The filenames mirror the
replay-backed e2e folders so architecture, verification, and maintenance use
one taxonomy.

## Files

- [Search](search.md)
  Explains global search and search-type filtering.
  Use it to review query behavior that is not scoped to one subreddit.
- [Feeds](feeds.md)
  Explains frontpage, all, popular, geo, pagination, and time-filtered feeds.
  Use it to review listing behavior driven by feed options.
- [Subreddit Posts](subreddit-posts.md)
  Explains subreddit-scoped search and post listing behavior.
  Use it to review behavior tied to one or more named subreddits.
- [Post Details](post-details.md)
  Explains post-detail and nested-comment extraction.
  Use it to review permalink-driven detail behavior.
- [User Data](user-data.md)
  Explains user activity scraping across posts and comments.
  Use it to review behavior centered on a Reddit username.
- [Retry](retry.md)
  Explains transient request retry and provider failure handling.
  Use it to review resilience around unstable Reddit requests.
- [Cache](cache.md)
  Explains API cache population, reuse, and caller-visible cache controls.
  Use it to review repeat request behavior.
- [Media](media.md)
  Explains media discovery, download policy, routing, limits, and media cache reuse.
  Use it to review binary media behavior.
- [Public Boundary And Errors](public-boundary-and-errors.md)
  Explains supported imports and failure translation.
  Use it to review cross-slice public API boundaries.
