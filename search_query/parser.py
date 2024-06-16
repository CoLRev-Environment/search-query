#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

from search_query.parser_ais import AISParser
from search_query.parser_cinahl import CINAHLParser
from search_query.parser_pubmed import PubmedParser
from search_query.parser_wos import WOSListParser
from search_query.parser_wos import WOSParser
from search_query.query import Query


def parse(query_str: str, query_type: str = "wos") -> Query:
    """Parse a query string."""
    if query_type == "wos":
        return WOSParser(query_str).parse()

    if query_type == "pubmed":
        return PubmedParser(query_str).parse()

    if query_type == "cinahl":
        return CINAHLParser(query_str).parse()

    if query_type == "wos_list":
        return WOSListParser(query_str).parse()

    if query_type == "ais_library":
        return AISParser(query_str).parse()

    raise ValueError(f"Invalid query type: {query_type}")
