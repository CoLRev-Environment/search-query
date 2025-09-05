#!/usr/bin/env python3
"""Versioned Web of Science parser wrappers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from search_query.wos.linter import WOSQueryListLinter
from search_query.wos.parser import WOSListParser, WOSParser

if TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class WOSParser_v1_0_0(WOSParser):
    """Web of Science parser for version 1.0.0."""

    VERSION = "1.0.0"


class WOSListParser_v1_0_0(WOSListParser):
    """Web of Science list parser for version 1.0.0."""

    VERSION = "1.0.0"

    def __init__(self, query_list: str, *, field_general: str = "") -> None:
        super().__init__(query_list=query_list, field_general=field_general)
        self.parser_class = WOSParser_v1_0_0
        self.linter = WOSQueryListLinter(self, WOSParser_v1_0_0)


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register these parsers with the ``registry``."""

    registry.register_parser_string(platform, version, WOSParser_v1_0_0)
    registry.register_parser_list(platform, version, WOSListParser_v1_0_0)
