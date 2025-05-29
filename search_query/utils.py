#!/usr/bin/env python3
"""Utilities for SearchQuery."""
import re
import typing

from search_query.constants import Colors


# pylint: disable=too-many-locals
def format_query_string_positions(
    query_str: str,
    positions: typing.List[typing.Tuple[int, int]],
    color: str = Colors.ORANGE,
) -> str:
    """Format the query string with multiple positions marked in color."""
    if not positions:
        return query_str

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

    if len(positions) == 1 and len(query_str) > 200:
        start, end = merged[0]

        # Define how much context you want (in words, not characters)
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
    return highlighted
