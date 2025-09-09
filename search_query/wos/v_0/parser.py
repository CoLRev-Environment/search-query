#!/usr/bin/env python3
"""Versioned Web of Science parser wrappers."""
from __future__ import annotations

import re
import typing

from search_query.wos.linter import WOSQueryListLinter
from search_query.wos.linter import WOSQueryStringLinter
from search_query.wos.parser import WOSListParser
from search_query.wos.parser import WOSParser

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry
    from search_query.query import Query


class WOSQueryStringLinter_v0(WOSQueryStringLinter):
    """Linter for WOS queries supporting deprecated fields."""

    VERSION = "0"
    VALID_fieldS_REGEX = re.compile(r"^[A-Za-z]{2,3}=$", re.IGNORECASE)

    def check_deprecated_field_tags(self, query: Query) -> None:
        """Allow field tags that were deprecated in later versions."""

        return


class WOSParser_v0(WOSParser):
    """Web of Science parser for version 0."""

    VERSION = "0"

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        query_str: str,
        *,
        field_general: str = "",
        offset: typing.Optional[dict] = None,
        original_str: typing.Optional[str] = None,
        silent: bool = False,
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_str,
            field_general=field_general,
            offset=offset,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter = WOSQueryStringLinter_v0(
            query_str=query_str,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )


class WOSListParser_v0(WOSListParser):
    """Web of Science list parser for version 0."""

    VERSION = "0"

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
        self.parser_class = WOSParser_v0
        self.linter = WOSQueryListLinter(
            parser=self,
            string_parser_class=WOSParser_v0,
            original_query_str=query_list,
            ignore_failing_linter=ignore_failing_linter,
        )


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register these parsers with the ``registry``."""

    registry.register_parser_string(platform, version, WOSParser_v0)
    registry.register_parser_list(platform, version, WOSListParser_v0)
