"""Version-aware parser dispatch."""

from __future__ import annotations

import typing as _t

from search_query.constants import PLATFORM
from search_query.exception import QuerySyntaxError
from search_query.query import Query

from search_query.pubmed.v1_0_0.parser import (
    PubMedListParser_v1_0_0,
    PubMedParser_v1_0_0,
)
from search_query.wos.v1_0_0.parser import (
    WOSListParser_v1_0_0,
    WOSParser_v1_0_0,
)
from search_query.ebsco.v1_0_0.parser import (
    EBSCOListParser_v1_0_0,
    EBSCOParser_v1_0_0,
)

if _t.TYPE_CHECKING:  # pragma: no cover
    from search_query.parser_base import QueryListParser, QueryStringParser


PARSERS: dict[str, dict[str, type["QueryStringParser"]]] = {
    PLATFORM.PUBMED.value: {"1.0.0": PubMedParser_v1_0_0},
    PLATFORM.WOS.value: {"1.0.0": WOSParser_v1_0_0},
    PLATFORM.EBSCO.value: {"1.0.0": EBSCOParser_v1_0_0},
}

LIST_PARSERS: dict[str, dict[str, type["QueryListParser"]]] = {
    PLATFORM.PUBMED.value: {"1.0.0": PubMedListParser_v1_0_0},
    PLATFORM.WOS.value: {"1.0.0": WOSListParser_v1_0_0},
    PLATFORM.EBSCO.value: {"1.0.0": EBSCOListParser_v1_0_0},
}

LATEST_VERSIONS: dict[str, str] = {
    PLATFORM.PUBMED.value: "1.0.0",
    PLATFORM.WOS.value: "1.0.0",
    PLATFORM.EBSCO.value: "1.0.0",
}


def _resolve_version(platform: str, version: str | None) -> str:
    if not version or version.lower() == "latest":
        return LATEST_VERSIONS[platform]
    return version


def _detect_is_list(query_str: str) -> bool:
    """Heuristic detection for list-style queries."""
    return "1." in query_str[:10]


def parse(
    query_str: str,
    *,
    field_general: str = "",
    platform: str = PLATFORM.WOS.value,
    parser_version: str | None = None,
    is_list: bool | None = None,
) -> Query:
    """Parse a query string using the versioned parsers."""

    platform = get_platform(platform)
    version = _resolve_version(platform, parser_version)
    is_list = _detect_is_list(query_str) if is_list is None else is_list
    try:
        if is_list:
            parser_cls = LIST_PARSERS[platform][version]
            parser = parser_cls(query_list=query_str, field_general=field_general)  # type: ignore
        else:
            parser_cls = PARSERS[platform][version]
            parser = parser_cls(query_str, field_general=field_general)  # type: ignore
        return parser.parse()
    except QuerySyntaxError:
        raise


def get_platform(platform_str: str) -> str:
    """Get canonical platform identifier from a string."""

    platform_str = platform_str.lower().rstrip().lstrip()
    if platform_str in [
        "web of science",
        "wos",
        "clarivate - web of science",
    ] or platform_str.startswith("web of science"):
        return PLATFORM.WOS.value

    if platform_str.startswith("ebsco"):
        return PLATFORM.EBSCO.value

    if platform_str.startswith("pubmed"):
        return PLATFORM.PUBMED.value

    if platform_str in ["embase.com", "embase"]:
        return "embase"
    if platform_str in ["medline"]:
        return "medline"
    if platform_str.startswith("ovid"):
        return "ovid"
    if platform_str.startswith("scopus"):
        return "scopus"
    if platform_str in ["scholar.google.com", "google scholar"]:
        return "google scholar"

    if platform_str.startswith("publish or perish"):
        return "publish or perish"

    if any(x in platform_str for x in ["psycinfo", "psychinfo"]):
        return "psycinfo"
    if platform_str in [
        "nlm",
        "national library of medicine",
        "u.s. national library of medicine",
    ]:
        return "nlm"

    raise ValueError(f"Invalid platform: {platform_str}")


__all__ = [
    "parse",
    "PARSERS",
    "LIST_PARSERS",
    "LATEST_VERSIONS",
    "get_platform",
]

