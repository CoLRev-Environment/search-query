#!/usr/bin/env python3
"""Versioned PubMed parser wrappers."""
from __future__ import annotations

from search_query.pubmed.linter import PubmedQueryListLinter
from search_query.pubmed.parser import PubmedListParser
from search_query.pubmed.parser import PubmedParser


class PubMedParser_v1_0_0(PubmedParser):
    """PubMed parser for version 1.0.0."""

    VERSION = "1.0.0"


class PubMedListParser_v1_0_0(PubmedListParser):
    """List-style PubMed parser for version 1.0.0."""

    VERSION = "1.0.0"

    def __init__(self, query_list: str, *, field_general: str = "") -> None:
        super().__init__(query_list=query_list, field_general=field_general)
        # Ensure versioned parser and linter are used
        self.parser_class = PubMedParser_v1_0_0
        self.linter = PubmedQueryListLinter(self, PubMedParser_v1_0_0)
