#!/usr/bin/env python3
"""Query linter hook."""
from __future__ import annotations

import typing
from pathlib import Path

import search_query.parser
from search_query.constants import ExitCodes
from search_query.search_file import load_search_file

if typing.TYPE_CHECKING:
    from search_query.parser_base import QueryStringParser
# pylint: disable=broad-except


def get_parser(
    search_string: str, *, syntax: str, search_field_general: str
) -> QueryStringParser:
    """Run the linter on the search string"""

    parser_class = search_query.parser.PARSERS[syntax]
    parser = parser_class(
        search_string, search_field_general=search_field_general
    )  # type: ignore

    try:
        parser.parse()
    except Exception as exc:
        print(f"Error parsing query: {exc}")
        assert parser.linter.messages  # type: ignore
    return parser


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

    parser = get_parser(
        search_file.search_string,
        syntax=search_file.platform,
        search_field_general=search_file.search_field,
    )

    if parser.linter.messages:
        return ExitCodes.FAIL

    print("No errors detected")
    return ExitCodes.SUCCESS
