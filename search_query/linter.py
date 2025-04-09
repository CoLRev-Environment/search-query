#!/usr/bin/env python3
"""Query linter hook."""
from __future__ import annotations

import sys

import search_query.parser
from search_query.constants import Colors
from search_query.constants import ExitCodes
from search_query.search_file import SearchFile
from search_query.utils import format_query_string_pos


def run_linter(search_string: str, platform: str) -> list:
    """Run the linter on the search string"""

    parser = search_query.parser.PARSERS[platform](search_string)
    try:
        parser.parse()
    except Exception:  # pylint: disable=broad-except
        assert parser.linter_messages
    return parser.linter_messages


def pre_commit_hook() -> int:
    """Entrypoint for the query linter hook"""

    file_path = sys.argv[1]

    try:
        search_file = SearchFile(file_path, platform="unknown")
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

    linter_messages = run_linter(search_file.search_string, platform)

    if linter_messages:
        for message in linter_messages:
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
