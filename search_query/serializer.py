#!/usr/bin/env python3
"""Version-aware serializer dispatch."""
from __future__ import annotations

from search_query.registry import (
    SERIALIZERS,
    LIST_SERIALIZERS,
    LATEST_SERIALIZERS,
    LATEST_LIST_SERIALIZERS,
    LATEST_VERSIONS_SERIALIZERS as LATEST_VERSIONS,
)
