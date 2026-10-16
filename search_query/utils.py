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


def _merge_positions(
    positions: typing.List[typing.Tuple[int, int]],
) -> typing.List[typing.List[int]]:
    """Sort and merge overlapping position ranges."""
    merged: typing.List[typing.List[int]] = []
    for start, end in sorted(positions, key=lambda position: position[0]):
        if merged and merged[-1][1] >= start:
            # Merge overlapping intervals
            merged[-1][1] = max(merged[-1][1], end)
        else:
            # Append new non-overlapping interval
            merged.append([start, end])
    return merged


def _format_same_line_positions(
    query_str: str,
    positions: typing.List[typing.Tuple[int, int]],
    color: str,
) -> str:
    """Render marked positions with short context from one query line."""
    sorted_positions = sorted(positions)
    result = []
    last_index = 0
    for start, end in sorted_positions:
        if not query_str[last_index:start].strip():
            continue
        result.append(query_str[last_index:start])
        result.append(f"{color}{query_str[start:end]}{Colors.END}")
        last_index = end
    if not result:
        return '""'
    result.append(query_str[last_index:])
    highlighted_query = "".join(result)

    line_start = highlighted_query.rfind("\n", 0, sorted_positions[0][0]) + 1
    line_end = highlighted_query.find("\n", sorted_positions[-1][1])
    if line_end == -1:
        line_end = len(highlighted_query)
    line = highlighted_query[line_start:line_end]
    before = f"{Colors.GREY}[...]{Colors.END}\n"
    after = f"\n{Colors.GREY}[...]{Colors.END}"
    return f"{before}{line}{after}".rstrip("\n").lstrip("\n")


def _format_long_query_position(
    query_str: str, start: int, end: int, color: str
) -> str:
    """Render one marked range with nearby words from a long query."""
    word_context = 8
    before_words = re.findall(r"\b\w+\b", query_str[:start])
    before_start = start
    if before_words:
        before_start = (
            query_str[:start].rfind(before_words[-word_context])
            if len(before_words) >= word_context
            else 0
        )

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


def _format_multiple_positions(
    query_str: str, merged: typing.List[typing.List[int]], color: str
) -> str:
    """Render all marked ranges in the full query string."""
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
    return highlighted.rstrip("\n").lstrip("\n")


def format_query_string_positions(
    query_str: str,
    positions: typing.List[typing.Tuple[int, int]],
    color: str = Colors.ORANGE,
) -> str:
    """Format the query string with multiple positions marked in color."""
    if not positions or list(set(positions))[0] == (-1, -1):
        return ""

    positions = [position for position in positions if position is not None]
    merged = _merge_positions(positions)
    if _is_same_line_error(positions, query_str):
        return _format_same_line_positions(query_str, positions, color)
    if len(positions) == 1 and len(query_str) > 200:
        start, end = merged[0]
        return _format_long_query_position(query_str, start, end, color)
    return _format_multiple_positions(query_str, merged, color)


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
            # Copy the message so aggregation doesn't mutate the original.
            copied_message = dict(message)
            if copied_message.get("position") is not None:
                copied_message["position"] = list(copied_message["position"])

            aggregated_messages.append(copied_message)
            message_index[key] = len(aggregated_messages) - 1
            continue

        aggregated_message = aggregated_messages[message_index[key]]

        aggregated_positions = aggregated_message.get("position")
        message_positions = message.get("position")
        if aggregated_positions is None or message_positions is None:
            continue

        for position in message_positions:
            if position not in aggregated_positions:
                aggregated_positions.append(position)

    return aggregated_messages
