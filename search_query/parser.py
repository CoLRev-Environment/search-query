#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

from search_query.constants import PLATFORM
from search_query.query import Query

# from search_query.parser_ebsco import EBSCOParser
# from search_query.parser_pubmed import PubmedListParser
# from search_query.parser_pubmed import PubmedParser
# from search_query.parser_wos import WOSListParser
# from search_query.parser_wos import WOSParser

PARSERS = {
    # PLATFORM.WOS.value: WOSParser,
    # PLATFORM.PUBMED.value: PubmedParser,
    # PLATFORM.EBSCO.value: EBSCOParser,
}

LIST_PARSERS = {
    # PLATFORM.WOS.value: WOSListParser,
    # PLATFORM.PUBMED.value: PubmedListParser,
    # PLATFORM.EBSCO.value: EBSCOParser,
}


# pylint: disable=too-many-return-statements
def parse(query_str: str, *, syntax: str = "wos") -> Query:
    """Parse a query string."""

    syntax = syntax.lower()

    if "1." in query_str[:10]:
        if syntax not in LIST_PARSERS:
            raise ValueError(f"Invalid syntax: {syntax}")

        return LIST_PARSERS[syntax](query_str).parse()

    if syntax not in PARSERS:
        raise ValueError(f"Invalid syntax: {syntax}")

    return PARSERS[syntax](query_str).parse()


def get_platform(platform_str: str) -> str:
    """Get the platform from the platform string"""

    platform_str = platform_str.lower().rstrip().lstrip()
    if platform_str in ["web of science", "wos"]:
        return PLATFORM.WOS.value

    raise ValueError(f"Invalid platform: {platform_str}")
