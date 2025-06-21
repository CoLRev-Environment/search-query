#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

import typing

from search_query.constants import LinterMode
from search_query.constants import PLATFORM
from search_query.ebsco.parser import EBSCOListParser
from search_query.ebsco.parser import EBSCOParser
from search_query.pubmed.parser import PubmedListParser
from search_query.pubmed.parser import PubmedParser
from search_query.query import Query
from search_query.wos.parser import WOSListParser
from search_query.wos.parser import WOSParser

if typing.TYPE_CHECKING:  # pragma: no cover
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
    field_general: str = "",
    platform: str = PLATFORM.WOS.value,
    mode: str = LinterMode.STRICT,
) -> Query:
    """Parse a query string."""
    platform = get_platform(platform)

    if "1." in query_str[:10]:
        if platform not in LIST_PARSERS:  # pragma: no cover
            raise ValueError(f"Invalid platform: {platform}")

        return LIST_PARSERS[platform](  # type: ignore
            query_list=query_str,
            field_general=field_general,
            mode=mode,
        ).parse()

    if platform not in PARSERS:  # pragma: no cover
        raise ValueError(f"Invalid platform: {platform}")

    parser_class = PARSERS[platform]

    query = parser_class(
        query_str, field_general=field_general, mode=mode
    ).parse()  # type: ignore

    return query


def get_platform(platform_str: str) -> str:
    """Get the platform from the platform string"""

    platform_str = platform_str.lower().rstrip().lstrip()
    if platform_str in ["web of science", "wos"]:
        return PLATFORM.WOS.value

    if platform_str in ["ebscohost", "ebsco"]:
        return PLATFORM.EBSCO.value

    if platform_str in ["pubmed"]:
        return PLATFORM.PUBMED.value

    raise ValueError(f"Invalid platform: {platform_str}")
