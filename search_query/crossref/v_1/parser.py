"""Version 1 Crossref parser registration."""
from __future__ import annotations

import typing

from search_query.crossref.parser import CrossrefListParser
from search_query.crossref.parser import CrossrefParser

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class CrossrefParser_v1(CrossrefParser):
    """Crossref parser for version 1."""

    VERSION = "1"


class CrossrefListParser_v1(CrossrefListParser):
    """Crossref list parser for version 1."""

    VERSION = "1"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register the version 1 Crossref parsers."""

    registry.register_parser_string(platform, version, CrossrefParser_v1)
    registry.register_parser_list(platform, version, CrossrefListParser_v1)
