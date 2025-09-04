#!/usr/bin/env python3
"""EBSCO translator for version 1.0.0."""
from __future__ import annotations

from search_query.ebsco.translator import EBSCOTranslator


class EBSCOTranslator_v1_0_0(EBSCOTranslator):
    """Translator for EBSCO queries."""

    VERSION = "1.0.0"
