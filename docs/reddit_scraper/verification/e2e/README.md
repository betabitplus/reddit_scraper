---
name: reddit-scraper-e2e-verification
doc_type: index
description: Index of Reddit scraper e2e verification docs. Use when you need the replay-backed proof doc for one vertical slice.
---

# E2E Verification

## Overview

These docs describe what each replay-backed e2e slice proves at the public
boundary. The filenames mirror the architecture concepts and the
`tests/reddit_scraper/e2e` slice folders.

## Files

- [Search](search.md)
  Explains global search and search-type filtering proofs.
  Use it to review query behavior outside a subreddit scope.
- [Feeds](feeds.md)
  Explains frontpage, all, popular, geo, pagination, and time-filtered listing proofs.
  Use it to review feed-style listing behavior.
- [Subreddit Posts](subreddit-posts.md)
  Explains subreddit-scoped search and subreddit post listing proofs.
  Use it to review behavior constrained by subreddit names.
- [Post Details](post-details.md)
  Explains permalink-driven post detail and nested-comment extraction proofs.
  Use it to review detail behavior for one post.
- [User Data](user-data.md)
  Explains user activity scraping proofs for posts and comments.
  Use it to review username-centered behavior.
- [Retry](retry.md)
  Explains replay-backed request resilience proofs.
  Use it to review resilience around unstable requests.
- [Cache](cache.md)
  Explains API cache population and reuse proofs.
  Use it to review repeat request behavior.
- [Media](media.md)
  Explains media discovery, download, and media cache reuse proofs.
  Use it to review binary media behavior.

## Hermetic Rule

Pytest e2e replay runs with committed VCR cassettes and JSON snapshots. Missing
cassettes must fail unless recording is explicitly requested.
