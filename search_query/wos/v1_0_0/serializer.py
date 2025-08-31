#!/usr/bin/env python3
"""Web of Science serializer for version 1.0.0."""
from __future__ import annotations

from search_query.wos.serializer import WOSQuerySerializer

# pylint: disable=too-few-public-methods


class WOSSerializer_v1_0_0(WOSQuerySerializer):
    """Web of Science serializer for version 1.0.0."""

    VERSION = "1.0.0"
