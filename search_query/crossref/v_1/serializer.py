"""Version 1 Crossref serializer registration."""
from __future__ import annotations

import typing

from search_query.crossref.serializer import CrossrefSerializer

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class CrossrefSerializer_v1(CrossrefSerializer):
    """Crossref serializer for version 1."""

    VERSION = "1"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register the version 1 Crossref serializers."""

    registry.register_serializer_string(platform, version, CrossrefSerializer_v1)
    registry.register_serializer_list(platform, version, CrossrefSerializer_v1)
