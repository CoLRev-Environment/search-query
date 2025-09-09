#!/usr/bin/env python3
"""Versioned EBSCO parser wrappers."""
from __future__ import annotations

import typing

from search_query.ebscohost.linter import EBSCOListLinter
from search_query.ebscohost.parser import EBSCOListParser
from search_query.ebscohost.parser import EBSCOParser

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry

# pylint: disable=too-few-public-methods


class EBSCOParser_v1(EBSCOParser):
    """EBSCO parser for version 1."""

    VERSION = "1"


class EBSCOListParser_v1(EBSCOListParser):
    """EBSCO list parser for version 1."""

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
        self.parser_class = EBSCOParser_v1
        self.linter = EBSCOListLinter(
            parser=self,
            string_parser_class=EBSCOParser_v1,
            ignore_failing_linter=ignore_failing_linter,
        )


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register these parsers with the ``registry``."""

    registry.register_parser_string(platform, version, EBSCOParser_v1)
    registry.register_parser_list(platform, version, EBSCOListParser_v1)
