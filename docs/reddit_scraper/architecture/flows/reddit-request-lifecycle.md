---
name: reddit-request-lifecycle
doc_type: architecture
description: High-level explanation of the Reddit JSON request lifecycle. Use when you need the runtime flow from public call to normalized result.
---

# Reddit Request Lifecycle

## Overview

This document describes the shared Reddit JSON request lifecycle used by
search, feed, post-detail, user-data, retry, and cache slices.

Question this diagram answers: How does a public call become a normalized
Reddit result?

```mermaid
sequenceDiagram
    participant Caller
    participant API as reddit_scraper API
    participant Runtime as _internal service
    participant Cache as cache manager
    participant Reddit as Reddit HTTP

    Caller->>API: call public function
    API->>Runtime: delegate with resolved options
    Runtime->>Cache: check first-page cache
    alt cache hit
        Cache-->>Runtime: cached payload
    else cache miss
        Runtime->>Reddit: GET with retry policy
        Reddit-->>Runtime: JSON payload
        Runtime->>Cache: store payload
    end
    Runtime-->>API: normalized result
    API-->>Caller: response DTO
```

## Main Flow

### Public Call

- Callers enter through the supported `reddit_scraper` root package.
- Facades resolve public options before delegating to private runtime services.
- Runtime services keep provider request details outside the public boundary.

### Provider Request

- First-page cache lookup may satisfy repeated requests.
- Cache misses perform Reddit HTTP requests with retry and stable logging.
- JSON payloads are parsed into normalized public result shapes.

### Boundary Return

- Successful flows return public response DTOs or result dictionaries.
- Provider, parse, and request failures are translated before crossing back to
  callers.

## Rules

- Log retries, cache hits/stores, notable decisions, parse failures, and
  operation durations with stable event names.
- Keep provider payload parsing private.
- Keep e2e replay focused on public calls, not private runtime methods.
