#!/usr/bin/env python3
"""Versioned Web of Science parser wrappers."""
from __future__ import annotations

import typing

from search_query.wos.linter import WOSQueryListLinter
from search_query.wos.parser import WOSListParser
from search_query.wos.parser import WOSParser

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry

# pylint: disable=duplicate-code


class WOSParser_v1(WOSParser):
    """Web of Science parser for version 1."""

    VERSION = "1"


class WOSListParser_v1(WOSListParser):
    """Web of Science list parser for version 1."""

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
        self.parser_class = WOSParser_v1
        self.linter = WOSQueryListLinter(
            parser=self,
            string_parser_class=WOSParser_v1,
            original_query_str=query_list,
            ignore_failing_linter=ignore_failing_linter,
        )


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register these parsers with the ``registry``."""

    registry.register_parser_string(platform, version, WOSParser_v1)
    registry.register_parser_list(platform, version, WOSListParser_v1)
