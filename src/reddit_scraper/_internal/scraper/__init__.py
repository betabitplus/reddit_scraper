"""Private scraper service package.

Why:
    Keeps the stateful Reddit client runtime under a real `_internal`
    subpackage while `_api` facades import through the private root.
"""

from __future__ import annotations
