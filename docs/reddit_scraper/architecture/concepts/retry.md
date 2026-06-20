---
name: reddit-retry
doc_type: architecture
description: Reddit retry behavior slice. Use when you need the model for transient failures and invalid-provider responses.
---

# Retry

## Overview

This document describes resilience around unstable Reddit requests. It defines
how transient request failures are retried and how provider failures become
public errors without leaking transport details.

Question this diagram answers: How does a failed request become either retry
success or a public error?

```mermaid
flowchart LR
    Request["Provider Request"] --> Failure["Transient Failure"]
    Failure --> Retry["Retry Policy"]
    Retry --> Success["Provider Success"]
    Retry --> Error["Public Scraper Error"]
```

## Main Model

### Retry Scope

- Retry behavior belongs around provider requests, not around caller input
  validation.
- Backoff and attempt limits are runtime policy, not public result data.
- Local deterministic retry probes may prove behavior without requiring Reddit
  instability.

### Failure Translation

- Invalid subreddit or provider errors should become public scraper failures.
- Exhausted retries should preserve enough context for callers to diagnose the
  failed operation.
- Immediate caller contract violations should not be hidden behind retry.

### Verification Mirror

- The `retry` e2e slice proves public invalid-provider behavior.
- Integration tests prove deterministic retry behavior against a local flaky
  endpoint without relying on Reddit instability.

## Rules

- Retry transient provider failures only.
- Translate exhausted provider failures at the public boundary.
- Keep retry policy mechanics private and boring.
