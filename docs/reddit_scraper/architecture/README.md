---
name: reddit-scraper-architecture
doc_type: index
description: Index of the Reddit scraper architecture docs. Use when you need to find the right architecture document.
---

# Architecture

## Overview

These docs describe how the Reddit scraper public boundary, private runtime,
and behavior slices fit together.

## Files

- [System](system.md)
  Shows how callers, `_api`, `_internal`, shared runtime, tests, and workbench fit.
  Use it to understand the integrated runtime story before reading a slice.
- [Concepts](concepts/README.md)
  Explains the stable vertical slices.
  Use it to find the architecture model for one supported behavior.
- [Flows](flows/README.md)
  Explains runtime request and replay lifecycles.
  Use it to understand how a public call moves through private runtime seams.
