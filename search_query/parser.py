#!/usr/bin/env python3
"""Version-aware parser dispatch."""
from __future__ import annotations

from search_query.constants import PLATFORM
from search_query.query import Query
from search_query.registry import LATEST_VERSIONS_PARSERS as LATEST_VERSIONS
from search_query.registry import LIST_PARSERS
from search_query.registry import PARSERS


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
    if is_list:
        parser_list_cls = LIST_PARSERS[platform][version]
        parser = parser_list_cls(
            query_list=query_str, field_general=field_general
        )  # type: ignore
    else:
        parser_cls = PARSERS[platform][version]
        parser = parser_cls(query_str, field_general=field_general)  # type: ignore
    return parser.parse()


def get_platform(platform_str: str) -> str:
    """Get canonical platform identifier from a string."""

    # pylint: disable=too-many-return-statements

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
