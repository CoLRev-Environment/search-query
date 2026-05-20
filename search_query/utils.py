#!/usr/bin/env python3
"""Utilities for SearchQuery."""
from __future__ import annotations

import re
import typing
from collections import OrderedDict

from search_query.constants import Colors


def _is_same_line_error(positions: list, query_str: str) -> bool:
    """Return True if all positions are on the same list query line."""
    if not positions or "\n" not in query_str:
        return False
    start = min(pos[0] for pos in positions)
    end = max(pos[1] for pos in positions)
    # Check if the position is on a single line
    single_line = query_str.count("\n", 0, start) == query_str.count("\n", 0, end)
    short_line = end - start < 100  # Arbitrary threshold for "short" line
    return single_line and short_line


# pylint: disable=too-many-branches
# pylint: disable=too-many-locals
def format_query_string_positions(
    query_str: str,
    positions: typing.List[typing.Tuple[int, int]],
    color: str = Colors.ORANGE,
) -> str:
    """Format the query string with multiple positions marked in color."""
    if not positions:
        return ""
    if list(set(positions))[0] == (-1, -1):
        return ""

    positions = [pos for pos in positions if pos is not None]

    # Sort and merge overlapping positions
    sorted_pos = sorted(positions, key=lambda x: x[0])
    merged: list = []
    for start, end in sorted_pos:
        if merged and merged[-1][1] >= start:
            # Merge overlapping intervals
            merged[-1][1] = max(merged[-1][1], end)
        else:
            # Append new non-overlapping interval
            merged.append([start, end])

    if _is_same_line_error(positions, query_str):
        # get line string surrounding the errors
        positions = sorted(positions)  # sort by start index
        result = []
        last_index = 0
        for start, end in positions:
            if not query_str[last_index:start].strip():
                continue
            result.append(query_str[last_index:start])
            result.append(f"{color}{query_str[start:end]}{Colors.END}")
            last_index = end
        if not result:
            return '""'
        result.append(query_str[last_index:])
        highlighted_query = "".join(result)

        # Find the line containing the error
        line_start = highlighted_query.rfind("\n", 0, positions[0][0]) + 1
        line_end = highlighted_query.find("\n", positions[-1][1])
        before = f"{Colors.GREY}[...]{Colors.END}\n"
        after = f"\n{Colors.GREY}[...]{Colors.END}"
        if line_end == -1:  # If no newline after end
            line_end = len(highlighted_query)
        line = highlighted_query[line_start:line_end]
        line = f"{before}{line}{after}".rstrip("\n").lstrip("\n")
        return line

    if len(positions) == 1 and len(query_str) > 200:
        start, end = merged[0]

        # Define the amount of context (in words, not characters)
        word_context = 8

        # Find words before
        before_words = re.findall(r"\b\w+\b", query_str[:start])
        before_start = start
        if before_words:
            before_start = (
                query_str[:start].rfind(before_words[-word_context])
                if len(before_words) >= word_context
                else 0
            )

        # Find words after
        after_words = re.findall(r"\b\w+\b", query_str[end:])
        after_end = end
        if after_words:
            match = re.search(
                re.escape(after_words[word_context - 1])
                if len(after_words) >= word_context
                else r"\w+$",
                query_str[end:],
            )
            if match:
                after_end = end + match.end()

        before = ""
        if before_start > 0:
            before += f"{Colors.GREY}[...]{Colors.END} "
        before += query_str[before_start:start]

        highlighted = f"{color}{query_str[start:end]}{Colors.END}".replace("\n", "")

        after = query_str[end:after_end]
        if after_end < len(query_str):
            after += f" {Colors.GREY}[...]{Colors.END}"

        return f"{before}{highlighted}{after}"

    # Apply formatting
    highlighted = ""
    last_index = 0
    for start, end in merged:
        # Add unhighlighted segment before this range
        highlighted += query_str[last_index:start]
        # Add highlighted segment
        highlighted += f"{color}{query_str[start:end]}{Colors.END}"
        last_index = end

    # Add remaining unhighlighted part
    highlighted += query_str[last_index:]

    highlighted = highlighted.rstrip("\n").lstrip("\n")
    return highlighted


def aggregate_linter_messages(
    messages: typing.Sequence[dict],
) -> typing.List[dict]:
    """Combine duplicate linter messages by aggregating their positions."""

    aggregated_messages: typing.List[dict] = []
    message_index: OrderedDict[typing.Tuple[typing.Any, ...], int] = OrderedDict()

    for message in messages:
        key = (
            message.get("code"),
            message.get("label"),
            message.get("message"),
            message.get("is_fatal"),
            message.get("details", ""),
        )

        if key not in message_index:
            # Copy the message so we don't mutate the original list.
            copied_message = {
                "code": message.get("code"),
                "label": message.get("label"),
                "message": message.get("message"),
                "is_fatal": message.get("is_fatal"),
                "details": message.get("details", ""),
                "position": None,
            }

            if message.get("position") is not None:
                copied_message["position"] = list(message["position"])

            aggregated_messages.append(copied_message)
            message_index[key] = len(aggregated_messages) - 1
            continue

        aggregated_message = aggregated_messages[message_index[key]]

        if aggregated_message["position"] is None or message.get("position") is None:
            continue

        for position in message["position"]:
            if position not in aggregated_message["position"]:
                aggregated_message["position"].append(position)

    return aggregated_messages
