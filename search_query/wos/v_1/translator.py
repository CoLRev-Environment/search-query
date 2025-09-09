#!/usr/bin/env python3
"""Web of Science translator for version 1."""
from __future__ import annotations

import typing

from search_query.wos.translator import WOSTranslator

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class WOSTranslator_v1(WOSTranslator):
    """Translator for WOS queries."""

    VERSION = "1"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register this translator with the ``registry``."""

    registry.register_translator(platform, version, WOSTranslator_v1)
