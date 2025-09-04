from __future__ import annotations
#!/usr/bin/env python3
from search_query.generic.serializer import GenericSerializer


class GenericSerializer_v_1_0_0(GenericSerializer):
    """Generic serializer for version 1.0.0."""

    VERSION = "1.0.0"


def register(registry, *, platform: str, version: str) -> None:
    registry.register_serializer_string(platform, version, GenericSerializer_v_1_0_0)
    registry.register_serializer_list(platform, version, GenericSerializer_v_1_0_0)
