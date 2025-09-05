#!/usr/bin/env python3
"""PubMed translator for version 1.0.0."""
from __future__ import annotations

from typing import TYPE_CHECKING

from search_query.pubmed.translator import PubmedTranslator

if TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class PubMedTranslator_v1_0_0(PubmedTranslator):
    """Translator for Pubmed queries."""

    VERSION = "1.0.0"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register this translator with the ``registry``."""

    registry.register_translator(platform, version, PubMedTranslator_v1_0_0)
