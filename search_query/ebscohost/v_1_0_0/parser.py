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


class EBSCOParser_v1_0_0(EBSCOParser):
    """EBSCO parser for version 1.0.0."""

    VERSION = "1.0.0"


class EBSCOListParser_v1_0_0(EBSCOListParser):
    """EBSCO list parser for version 1.0.0."""

    VERSION = "1.0.0"

    def __init__(self, query_list: str, *, field_general: str = "") -> None:
        super().__init__(query_list=query_list, field_general=field_general)
        self.parser_class = EBSCOParser_v1_0_0
        self.linter = EBSCOListLinter(self, EBSCOParser_v1_0_0)


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register these parsers with the ``registry``."""

    registry.register_parser_string(platform, version, EBSCOParser_v1_0_0)
    registry.register_parser_list(platform, version, EBSCOListParser_v1_0_0)
