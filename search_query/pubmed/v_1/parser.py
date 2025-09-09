#!/usr/bin/env python3
"""Versioned PubMed parser wrappers."""
from __future__ import annotations

import typing

from search_query.pubmed.linter import PubmedQueryListLinter
from search_query.pubmed.parser import PubmedListParser
from search_query.pubmed.parser import PubmedParser

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry

# pylint: disable=duplicate-code


class PubMedParser_v1(PubmedParser):
    """PubMed parser for version 1."""

    VERSION = "1"


class PubMedListParser_v1(PubmedListParser):
    """List-style PubMed parser for version 1."""

    VERSION = "1"

    def __init__(
        self,
        query_list: str,
        *,
        field_general: str = "",
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_list=query_list,
            field_general=field_general,
            ignore_failing_linter=ignore_failing_linter,
        )
        # Ensure versioned parser and linter are used
        self.parser_class = PubMedParser_v1
        self.linter = PubmedQueryListLinter(
            self,
            PubMedParser_v1,
            ignore_failing_linter=ignore_failing_linter,
        )


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register these parsers with the ``registry``."""

    registry.register_parser_string(platform, version, PubMedParser_v1)
    registry.register_parser_list(platform, version, PubMedListParser_v1)
