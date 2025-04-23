#!/usr/bin/env python3
"""Query linter hook."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import search_query.parser
from search_query.constants import Colors
from search_query.constants import ExitCodes
from search_query.utils import format_query_string_positions
from search_query.search_file import SearchFile


def run_linter(search_string: str, *, syntax: str, search_field_general: str) -> list:
    """Run the linter on the search string"""

    parser_class = search_query.parser.PARSERS[syntax]
    parser = parser_class(search_string, search_field_general, verbosity=0)  # type: ignore

    try:
        parser.parse()
    except Exception:  # pylint: disable=broad-except
        assert parser.linter.messages  # type: ignore
    return parser.linter.messages  # type: ignore


# pylint: disable=too-many-locals
def pre_commit_hook(file_path: str) -> int:
    """Entrypoint for the query linter hook"""

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

    messages = run_linter(
        search_file.search_string,
        syntax=search_file.platform,
        search_field_general=search_file.search_field,
    )

    print(f"Lint: {Path(file_path).name} ({platform})")
    if messages:
        grouped_messages = defaultdict(list)

        for message in messages:
            grouped_messages[message["code"]].append(message)

        for code, group in grouped_messages.items():
            # Take the first message as representative
            representative = group[0]
            color = Colors.ORANGE
            category = "Info"

            if representative["is_fatal"]:
                color = Colors.RED
                category = "Fatal"
            elif code.startswith("E"):
                category = "Error"
            elif code.startswith("W"):
                category = "Warning"

            print(
                f"- {color}{category}{Colors.END}: "
                f"{representative['label']} ({code})"
            )
            consolidated_messages = []
            for message in group:
                if message["details"]:
                    consolidated_messages.append(f"  {message['details']}")
                else:
                    consolidated_messages.append(f"  {message['message']}")
            for item in set(consolidated_messages):
                print(item)
            positions = list(message["position"] for message in group)
            query_info = format_query_string_positions(
                search_file.search_string,
                positions,
                color=color,
            )
            print(f"  {query_info}")

        # TODO : only fail when fatal (linter-mode)?
        return ExitCodes.FAIL

    print("No errors detected")

    return ExitCodes.SUCCESS
