#!/usr/bin/env python3
"""Web of Science translator for version 1.0.0."""
from __future__ import annotations

from search_query.wos.translator import WOSTranslator


class WOSTranslator_v1_0_0(WOSTranslator):
    """Translator for WOS queries."""

    VERSION = "1.0.0"


def register(registry, *, platform: str, version: str) -> None:
    registry.register_translator(platform, version, WOSTranslator_v1_0_0)
