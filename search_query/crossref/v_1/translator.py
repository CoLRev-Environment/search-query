"""Version 1 Crossref translator registration."""
from __future__ import annotations

import typing

from search_query.crossref.translator import CrossrefTranslator

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class CrossrefTranslator_v1(CrossrefTranslator):
    """Crossref translator for version 1."""

    VERSION = "1"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register the version 1 Crossref translator."""

    registry.register_translator(platform, version, CrossrefTranslator_v1)
