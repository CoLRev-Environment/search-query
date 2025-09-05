#!/usr/bin/env python3
"""EBSCO serializer for version 1.0.0."""
from __future__ import annotations

import typing

from search_query.ebscohost.serializer import EBSCOQuerySerializer

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


# pylint: disable=too-few-public-methods
class EBCOSerializer_v1_0_0(EBSCOQuerySerializer):
    """EBSCO serializer for version 1.0.0."""

    VERSION = "1.0.0"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register this serializer with the ``registry``."""

    registry.register_serializer_string(platform, version, EBCOSerializer_v1_0_0)
    registry.register_serializer_list(platform, version, EBCOSerializer_v1_0_0)
