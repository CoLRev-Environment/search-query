#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

from search_query.parser_ais import AISParser
from search_query.parser_ebsco import EBSCOParser
from search_query.parser_pubmed import PubmedListParser
from search_query.parser_pubmed import PubmedParser
from search_query.parser_wos import WOSListParser
from search_query.parser_wos import WOSParser
from search_query.query import Query


# pylint: disable=too-many-return-statements
def parse(query_str: str, *, syntax: str = "wos") -> Query:
    """Parse a query string."""

    syntax = syntax.lower()

    if syntax in ["wos", "web of science"]:
        if "1." in query_str[:10]:
            return WOSListParser(query_str).parse()
        return WOSParser(query_str).parse()
    if syntax in ["wos_list"]:
        return WOSListParser(query_str).parse()

    if syntax in ["pubmed"]:
        if "1." in query_str[:10]:
            return PubmedListParser(query_str).parse()
        return PubmedParser(query_str).parse()

    if syntax in ["cinahl"]:
        return EBSCOParser(query_str).parse()

    if syntax in ["ais_library"]:
        return AISParser(query_str).parse()

    raise ValueError(f"Invalid query type: {syntax}")
