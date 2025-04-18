#!/usr/bin/env python3
"""Query linter hook."""
from __future__ import annotations

import sys
from abc import ABCMeta

import search_query.parser
from search_query.constants import Colors
from search_query.constants import ExitCodes
from search_query.search_file import load_search_file
from search_query.utils import format_query_string_pos


def run_linter(search_string: str, *, syntax: str, search_field_general: str) -> list:
    """Run the linter on the search string"""

    parser_class = search_query.parser.PARSERS[syntax]
    if isinstance(parser_class, ABCMeta):
        raise NotImplementedError(
            f"Cannot instantiate {parser_class} because it is abstract."
        )
    parser = parser_class(search_string, search_field_general)

    try:
        parser.parse()
    except Exception:  # pylint: disable=broad-except
        assert parser.linter.messages
    return parser.linter.messages


def pre_commit_hook() -> int:
    """Entrypoint for the query linter hook"""

    file_path = sys.argv[1]

    try:
        search_file = load_search_file(file_path)
        platform = search_query.parser.get_platform(search_file.platform)
    except Exception as e:  # pylint: disable=broad-except
        print(e)
        return ExitCodes.FAIL

    if platform not in search_query.parser.PARSERS:
        print(
            f"Unknown platform: {platform}."
            f"Must be one of {search_query.parser.PARSERS}"
        )
        return ExitCodes.FAIL

    messages = run_linter(
        search_file.search_string,
        syntax=search_file.platform,
        search_field_general=search_file.search_field,
    )

    if messages:
        for message in messages:
            color = Colors.ORANGE
            if message["level"] == "error":
                color = Colors.RED

            print(f"{file_path} ({platform})")
            print(f"- {message['msg']}")
            query_info = format_query_string_pos(
                search_file.search_string, message["pos"], color=color
            )
            print(f"  {query_info}")

        return ExitCodes.FAIL

    return ExitCodes.SUCCESS


def main() -> None:
    """Main entrypoint for the query linter hook"""
    raise SystemExit(pre_commit_hook())


if __name__ == "__main__":
    main()
