#!/usr/bin/env python3
"""Utilities for SearchQuery."""
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


def print_tokens(tokens: list) -> None:
    """Print the tokens in a formatted table."""
    for token in tokens:
        print(f"{token.value:<30} {token.type:<40} {str(token.position):<10}")
