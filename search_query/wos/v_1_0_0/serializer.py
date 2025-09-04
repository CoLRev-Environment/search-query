#!/usr/bin/env python3
"""Web of Science serializer for version 1.0.0."""
from __future__ import annotations

from search_query.wos.serializer import WOSQuerySerializer

# pylint: disable=too-few-public-methods


class WOSSerializer_v1_0_0(WOSQuerySerializer):
    """Web of Science serializer for version 1.0.0."""

    VERSION = "1.0.0"


def register(registry, *, platform: str, version: str) -> None:
    registry.register_serializer_string(platform, version, WOSSerializer_v1_0_0)
    registry.register_serializer_list(platform, version, WOSSerializer_v1_0_0)
