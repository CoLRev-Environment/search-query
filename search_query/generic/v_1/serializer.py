#!/usr/bin/env python3
"""Generic serializer for version 1."""
from __future__ import annotations

import typing

from search_query.generic.serializer import GenericSerializer

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


# pylint: disable=too-few-public-methods
class GenericSerializer_v1(GenericSerializer):
    """Generic serializer for version 1."""

    VERSION = "1"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register this serializer with the ``registry``."""

    registry.register_serializer_string(platform, version, GenericSerializer_v1)
    registry.register_serializer_list(platform, version, GenericSerializer_v1)
