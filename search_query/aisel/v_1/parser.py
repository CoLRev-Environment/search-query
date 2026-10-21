"""Version 1 AIS eLibrary parser registration."""
from __future__ import annotations

import typing

from search_query.aisel.parser import AISListParser
from search_query.aisel.parser import AISParser

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class AISParser_v1(AISParser):
    """AIS eLibrary parser for version 1."""

    VERSION = "1"


class AISListParser_v1(AISListParser):
    """AIS eLibrary list parser for version 1."""

    VERSION = "1"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register the version 1 AIS eLibrary parsers."""
    registry.register_parser_string(platform, version, AISParser_v1)
    registry.register_parser_list(platform, version, AISListParser_v1)
