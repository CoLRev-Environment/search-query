#!/usr/bin/env python3
"""Query linter hook."""
from __future__ import annotations

from pathlib import Path

import search_query.parser
from search_query.constants import Colors
from search_query.constants import ExitCodes
from search_query.search_file import load_search_file
from search_query.utils import format_query_string_pos


def run_linter(search_string: str, *, syntax: str, search_field_general: str) -> list:
    """Run the linter on the search string"""

    parser_class = search_query.parser.PARSERS[syntax]
    parser = parser_class(search_string, search_field_general)  # type: ignore

    try:
        parser.parse()
    except Exception:  # pylint: disable=broad-except
        assert parser.linter.messages  # type: ignore
    return parser.linter.messages  # type: ignore


def pre_commit_hook(file_path: str) -> int:
    """Entrypoint for the query linter hook"""

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

    print(f"Lint: {Path(file_path).name} ({platform})")
    if messages:
        for message in messages:
            color = Colors.ORANGE

            if message["is_fatal"]:
                color = Colors.RED

            category = "Fatal"
            if message["code"].startswith("E"):
                category = "Error"
            elif message["code"].startswith("W"):
                category = "Warning"

            print(
                f"- {color}{category}{Colors.END}: "
                f"{message['label']} ({message['code']})"
            )
            query_info = format_query_string_pos(
                search_file.search_string, message["position"], color=color
            )
            if message["details"]:
                print(f"  {message['details']}")
            else:
                print(f"  {message['message']}")
            print(f"  {query_info}")

        return ExitCodes.FAIL

    print("No errors detected")

    return ExitCodes.SUCCESS
