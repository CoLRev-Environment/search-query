#!/usr/bin/env python3
"""Versioned EBSCO parser wrappers."""
from __future__ import annotations

from search_query.ebsco.linter import EBSCOListLinter
from search_query.ebsco.parser import EBSCOListParser
from search_query.ebsco.parser import EBSCOParser

# pylint: disable=too-few-public-methods


class EBSCOParser_v1_0_0(EBSCOParser):
    """EBSCO parser for version 1.0.0."""

    VERSION = "1.0.0"

    # TODO : check whether this is valid! -
    # generally move functionality to the modules one directory up?!
    # TODO : switch tests to the verisoned parser!


class EBSCOListParser_v1_0_0(EBSCOListParser):
    """EBSCO list parser for version 1.0.0."""

    VERSION = "1.0.0"

    def __init__(self, query_list: str, *, field_general: str = "") -> None:
        super().__init__(query_list=query_list, field_general=field_general)
        self.parser_class = EBSCOParser_v1_0_0
        self.linter = EBSCOListLinter(self, EBSCOParser_v1_0_0)
