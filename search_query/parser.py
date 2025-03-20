#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

from search_query.constants import LinterMode
from search_query.constants import PLATFORM
from search_query.parser_wos import WOSListParser
from search_query.parser_wos import WOSParser
from search_query.query import Query

# from search_query.parser_ebsco import EBSCOParser
# from search_query.parser_pubmed import PubmedListParser
# from search_query.parser_pubmed import PubmedParser

PARSERS = {
    PLATFORM.WOS.value: WOSParser,
    # PLATFORM.PUBMED.value: PubmedParser,
    # PLATFORM.EBSCO.value: EBSCOParser,
}

LIST_PARSERS = {
    PLATFORM.WOS.value: WOSListParser,
    # PLATFORM.PUBMED.value: PubmedListParser,
    # PLATFORM.EBSCO.value: EBSCOParser,
}


# pylint: disable=too-many-return-statements
def parse(
    query_str: str,
    search_fields: str,
    *,
    syntax: str = "wos",
    mode: LinterMode = LinterMode.STRICT,
) -> Query:
    """Parse a query string."""
    syntax = syntax.lower()

    if "1." in query_str[:10]:
        if syntax not in LIST_PARSERS:
            raise ValueError(f"Invalid syntax: {syntax}")

        return LIST_PARSERS[syntax](query_str, search_fields, mode).parse()

    if syntax not in PARSERS:
        raise ValueError(f"Invalid syntax: {syntax}")

    return PARSERS[syntax](query_str, search_fields, mode).parse()


def get_platform(platform_str: str) -> str:
    """Get the platform from the platform string"""

    platform_str = platform_str.lower().rstrip().lstrip()
    if platform_str in ["web of science", "wos"]:
        return PLATFORM.WOS.value

    raise ValueError(f"Invalid platform: {platform_str}")
