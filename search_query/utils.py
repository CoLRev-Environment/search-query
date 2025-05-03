#!/usr/bin/env python3
"""Utilities for SearchQuery."""
import typing

from search_query.constants import Colors


def format_query_string_pos(
    query_str: str, pos: tuple, color: str = Colors.ORANGE
) -> str:
    """Format the query string with the position of the error marked in orange."""
    return (
        query_str[: pos[0]]
        + f"{color}{query_str[pos[0]:pos[1]]}{Colors.END}"
        + query_str[pos[1] :]
    )


def format_query_string_positions(
    query_str: str,
    positions: typing.List[typing.Tuple[int, int]],
    color: str = Colors.ORANGE,
) -> str:
    """Format the query string with multiple positions marked in color."""
    if not positions:
        return query_str

    # Sort and merge overlapping positions
    sorted_pos = sorted(positions, key=lambda x: x[0])
    merged: list = []
    for start, end in sorted_pos:
        if not merged or merged[-1][1] < start:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

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
