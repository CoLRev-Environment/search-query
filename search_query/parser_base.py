#!/usr/bin/env python3
"""Base query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import Colors
from search_query.query import Query


# pylint: disable=too-few-public-methods
class QueryParser:
    """QueryParser class"""

    def __init__(self, query_str: str) -> None:
        self.query_str = query_str


class QueryStringParser(QueryParser):
    """QueryStringParser"""

    tokens: list

    def get_token_types(self, tokens: list, *, legend: bool = False) -> str:
        """Print the token types"""

        mismatch = False

        for i in range(len(tokens) - 1):
            _, (_, current_end) = tokens[i]
            _, (next_start, _) = tokens[i + 1]
            if current_end + 1 != next_start:
                if re.match(r"\s*", self.query_str[current_end:next_start]):
                    continue
                # Position mismatch means: not tokenized
                print(
                    "NOT-TOKENIZED: "
                    f"{Colors.RED}{self.query_str[current_end:next_start]}{Colors.END} "
                    f"(positions {current_end}-{next_start} in query_str)"
                )
                mismatch = True

        output = ""
        for token, _ in tokens:
            if self.is_term(token):
                output += token
            elif self.is_search_field(token):
                output += f"{Colors.GREEN}{token}{Colors.END}"
            elif self.is_operator(token):
                output += f" {Colors.ORANGE}{token}{Colors.END} "
            elif self.is_parenthesis(token):
                output += f"{Colors.BLUE}{token}{Colors.END}"
            else:
                output += f"{Colors.RED}{token}{Colors.END}"

        if legend:
            output += f"\n Term\n {Colors.BLUE}Parenthesis{Colors.END}"
            output += f"\n {Colors.GREEN}Search field{Colors.END}"
            output += f"\n {Colors.ORANGE}Operator {Colors.END}"
            output += f"\n {Colors.RED}NOT-MATCHED{Colors.END}"
        if mismatch:
            raise ValueError
        return output

    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        raise NotImplementedError(
            "is_search_field method must be implemented by inheriting classes"
        )

    def is_parenthesis(self, token: str) -> bool:
        """Token is parenthesis"""
        return token in ["(", ")"]

    def is_operator(self, token: str) -> bool:
        """Token is operator"""
        return bool(re.match(r"^(AND|OR|NOT)$", token, re.IGNORECASE))

    def is_term(self, token: str) -> bool:
        """Check if a token is a term."""
        return (
            not self.is_operator(token)
            and not self.is_parenthesis(token)
            and not self.is_search_field(token)
        )


# pylint: disable=too-few-public-methods
class QueryListParser(QueryParser):
    """QueryListParser"""

    tokens: typing.Dict[str, str] = {}

    def is_or_node(self, node_content: str) -> bool:
        """Node content is OR node"""
        raise NotImplementedError

    def is_and_node(self, node_content: str) -> bool:
        """Node content is AND node"""
        raise NotImplementedError

    def parse_list(self) -> None:
        """Tokenize the query_str."""
        raise NotImplementedError

    def get_children(self, node_content: str) -> list:
        """Get the children of a node."""
        raise NotImplementedError

    def parse_term_node(self, term_str: str) -> Query:
        """Parse a term node."""
        raise NotImplementedError

    def is_term(self, token: str) -> bool:
        """Check if a token is a term."""
        return not self.is_or_node(token) and not self.is_and_node(token)

    def print_term_token_types(self, token_content: str) -> str:
        """Override with method to parse and print term node types."""
        return token_content

    def get_token_types(self, tokens: dict) -> str:
        """Print the token types"""

        output = ""
        for token_nr, token_content in tokens.items():
            output += f"{token_nr}: "
            if self.is_term(token_content):
                output += self.print_term_token_types(token_content)
            # elif self.is_search_field(token_content):
            #     output += f"{Colors.GREEN}{token_content}{Colors.END}"
            elif self.is_or_node(token_content) or self.is_and_node(token_content):
                output += f" {Colors.ORANGE}{token_content}{Colors.END} "
            # elif self.is_parenthesis(token_content):
            #     output += f"{Colors.BLUE}{token_content}{Colors.END}"
            else:
                output += f"{Colors.RED}{token_content}{Colors.END}"
            output += "\n"

        output += f"\n Term\n {Colors.BLUE}Parenthesis{Colors.END}"
        output += f"\n {Colors.GREEN}Search field{Colors.END}"
        output += f"\n {Colors.ORANGE}Operator {Colors.END}"
        output += f"\n {Colors.RED}NOT-MATCHED{Colors.END}"
        return output

    def parse_node(self, node_nr: str) -> Query:
        """Parse a node from the node list."""

        if self.is_or_node(self.tokens[node_nr]):
            node = Query(value="OR", operator=True)
            for child in self.get_children(self.tokens[node_nr]):
                node.children.append(self.parse_node(child))
            return node

        if self.is_and_node(self.tokens[node_nr]):
            node = Query(value="AND", operator=True)
            for child in self.get_children(self.tokens[node_nr]):
                node.children.append(self.parse_node(child))
            return node

        return self.parse_term_node(self.tokens[node_nr])

    def parse(self) -> Query:
        """Parse a query string."""

        self.parse_list()
        node = self.parse_node(list(self.tokens.keys())[-1])
        return node
