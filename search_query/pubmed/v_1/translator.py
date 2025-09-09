#!/usr/bin/env python3
"""PubMed translator for version 1."""
from __future__ import annotations

import typing

from search_query.pubmed.translator import PubmedTranslator

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class PubMedTranslator_v1(PubmedTranslator):
    """Translator for Pubmed queries."""

    VERSION = "1"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register this translator with the ``registry``."""

    registry.register_translator(platform, version, PubMedTranslator_v1)
