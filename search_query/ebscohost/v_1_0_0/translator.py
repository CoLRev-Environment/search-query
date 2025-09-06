#!/usr/bin/env python3
"""EBSCO translator for version 1.0.0."""
from __future__ import annotations

import typing

from search_query.ebscohost.translator import EBSCOTranslator

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class EBSCOTranslator_v1_0_0(EBSCOTranslator):
    """Translator for EBSCO queries."""

    VERSION = "1.0.0"


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register this translator with the ``registry``."""

    registry.register_translator(platform, version, EBSCOTranslator_v1_0_0)
