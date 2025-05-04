#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

import typing

from search_query.constants import LinterMode
from search_query.constants import PLATFORM
from search_query.parser_ebsco import EBSCOListParser
from search_query.parser_ebsco import EBSCOParser
from search_query.parser_pubmed import PubmedListParser
from search_query.parser_pubmed import PubmedParser
from search_query.parser_wos import WOSListParser
from search_query.parser_wos import WOSParser
from search_query.query import Query

if typing.TYPE_CHECKING:
    from search_query.parser_base import QueryListParser
    from search_query.parser_base import QueryStringParser

PARSERS: typing.Dict[str, type[QueryStringParser]] = {
    PLATFORM.WOS.value: WOSParser,
    PLATFORM.PUBMED.value: PubmedParser,
    PLATFORM.EBSCO.value: EBSCOParser,
}

LIST_PARSERS: typing.Dict[str, type[QueryListParser]] = {
    PLATFORM.WOS.value: WOSListParser,
    PLATFORM.PUBMED.value: PubmedListParser,
    PLATFORM.EBSCO.value: EBSCOListParser,
}


# pylint: disable=too-many-return-statements
def parse(
    query_str: str,
    *,
    search_field_general: str = "",
    platform: str = "wos",
    mode: str = LinterMode.STRICT,
) -> Query:
    """Parse a query string."""
    platform = platform.lower()

    if "1." in query_str[:10]:
        if platform not in LIST_PARSERS:
            raise ValueError(f"Invalid platform: {platform}")

        string_parser = PARSERS[platform]

        return LIST_PARSERS[platform](
            query_list=query_str,
            parser_class=string_parser,
            search_field_general=search_field_general,
            mode=mode,
        ).parse()

    if platform not in PARSERS:
        raise ValueError(f"Invalid platform: {platform}")

    parser_class = PARSERS[platform]

    return parser_class(
        query_str, search_field_general=search_field_general, mode=mode
    ).parse()  # type: ignore


def get_platform(platform_str: str) -> str:
    """Get the platform from the platform string"""

    platform_str = platform_str.lower().rstrip().lstrip()
    if platform_str in ["web of science", "wos"]:
        return PLATFORM.WOS.value

    if platform_str in ["ebscohost", "ebsco"]:
        return PLATFORM.EBSCO.value

    raise ValueError(f"Invalid platform: {platform_str}")
