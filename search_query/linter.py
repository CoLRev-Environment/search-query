#!/usr/bin/env python3
"""Query linter hook."""
from __future__ import annotations

import typing
from pathlib import Path

import search_query.parser
from search_query.constants import ExitCodes
from search_query.search_file import load_search_file
from search_query.search_file import SearchFile

if typing.TYPE_CHECKING:
    from search_query.parser_base import QueryStringParser
# pylint: disable=broad-except


def _run_parser(
    search_string: str, *, platform: str, field_general: str
) -> QueryStringParser:
    """Run the linter on the search string"""

    platform = search_query.parser.get_platform(platform)
    version = search_query.parser.LATEST_VERSIONS[platform]
    if "1." in search_string:
        parser_class = search_query.parser.LIST_PARSERS[platform][version]

    else:
        parser_class = search_query.parser.PARSERS[platform][version]
    parser = parser_class(search_string, field_general=field_general)  # type: ignore

    try:
        parser.parse()
    except Exception:
        assert parser.linter.messages  # type: ignore

    if parser.linter.messages == {-1: []}:
        parser.linter.messages = {}
    return parser


def lint_file(search_file: SearchFile) -> dict:
    """Lint a search file and return the messages."""
    platform = search_query.parser.get_platform(search_file.platform)
    if platform not in search_query.parser.PARSERS:
        raise ValueError(
            f"Unknown platform: {platform}. "
            f"Must be one of {search_query.parser.PARSERS}"
        )

    return lint_query_string(
        search_file.search_string,
        platform=platform,
        field_general=search_file.field,
    )


def lint_query_string(
    search_string: str,
    *,
    platform: str,
    field_general: str = "",
) -> dict:
    """Lint a query string and return the messages."""
    # pylint: disable=too-many-locals
    if platform not in search_query.parser.PARSERS:
        raise ValueError(
            f"Unknown platform: {platform}. "
            f"Must be one of {search_query.parser.PARSERS}"
        )

    print(f"Linting query string for platform {platform}")

    parser = _run_parser(search_string, platform=platform, field_general=field_general)

    return parser.linter.messages  # type: ignore


# pylint: disable=too-many-locals
def pre_commit_hook(file_path: str) -> int:
    """Entrypoint for the query linter hook"""

    try:
        search_file = load_search_file(file_path)
        platform = search_query.parser.get_platform(search_file.platform)
    except ValueError as e:
        print(e)
        return ExitCodes.FAIL

    if platform not in search_query.parser.PARSERS:
        print(
            f"Unknown platform: {platform}."
            f"Must be one of {search_query.parser.PARSERS}"
        )
        return ExitCodes.FAIL

    print(f"Lint: {Path(file_path).name} ({platform})")

    parser = _run_parser(
        search_file.search_string,
        platform=search_file.platform,
        field_general=search_file.field,
    )

    if parser.linter.messages:
        return ExitCodes.FAIL

    print("No errors detected")
    return ExitCodes.SUCCESS
