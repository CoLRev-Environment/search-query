#!/usr/bin/env python3
"""PubMed translator for version 1.0.0."""
from __future__ import annotations

from search_query.pubmed.translator import PubmedTranslator


class PubMedTranslator_v1_0_0(PubmedTranslator):
    """Translator for Pubmed queries."""

    VERSION = "1.0.0"
