#!/usr/bin/env python3
"""WOS query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import Operators
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query


class WOSParser(QueryStringParser):
    """Parser for Web of Science queries."""

    # https://images.webofknowledge.com/images/help/WOS/hs_advanced_fieldtags.html
    search_field_regex = r"[A-Z]+="
    boolean_operators_regex = r"\b(AND|OR|NOT)\b"
    proximity_search_regex = r"\bNEAR\/\d+"
    parentheses_regex = r"\(|\)"
    quoted_string_regex = r"\"[^\"]*\""
    string_regex = (
        r"\b(?!(?:AND|OR|NOT|NEAR)\b)[\w\?\$-]+"
        + r"(?:\s+(?!(?:AND|OR|NOT|NEAR)\b)[\w\?\$-]+)*\*?"
    )

    pattern = "|".join(
        [
            search_field_regex,
            boolean_operators_regex,
            proximity_search_regex,
            parentheses_regex,
            quoted_string_regex,
            string_regex,
        ]
    )

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str.replace("”", '"').replace("“", '"')

        tokens = [
            (m.group(0), (m.start(), m.end()))
            for m in re.finditer(self.pattern, query_str, re.IGNORECASE)
        ]
        self.tokens = [(token.strip(), pos) for token, pos in tokens if token.strip()]

    def is_search_field(self, token: str) -> bool:
        return bool(re.search(r"^[A-Z]+=$", token))

    def is_operator(self, token: str) -> bool:
        """Token is operator"""
        return bool(re.match(r"^(AND|OR|NOT|NEAR/\d+)$", token, re.IGNORECASE))

    def parse_node(
        self, tokens: list, search_field: str = "", unary_not: bool = False
    ) -> Query:
        """Parse a node from a list of tokens."""

        node = self._initialize_node(search_field, unary_not)
        current_operator = ""
        expecting_operator = False

        while tokens:
            if unary_not and len(node.children) > 0:
                break
            next_item, pos = self._get_next_item(tokens)
            if self.is_search_field(next_item):
                search_field = next_item
                next_item, pos = self._get_next_item(tokens)
            if next_item == ")":
                # Make sure we dont' read "()" (empty parentheses)
                assert len(node.children) > 0
                break

            if self.is_term(next_item):
                node = self._handle_term(node, next_item, search_field, pos)
                expecting_operator = True
                continue

            if next_item.upper().startswith("NEAR"):
                assert expecting_operator
                node, current_operator = self._handle_near(
                    node, next_item, pos, current_operator
                )
                continue

            if next_item.upper() in [Operators.AND, Operators.OR]:
                assert expecting_operator
                node, current_operator = self._handle_and_or(
                    node, next_item, pos, current_operator
                )
                continue

            if next_item.upper() == Operators.NOT:
                assert expecting_operator
                node = self._handle_not(node, tokens, search_field, current_operator)
                continue

            if next_item == "(":
                node.children.append(self.parse_node(tokens, search_field))
                expecting_operator = True

        # Single-element parenthesis
        if node.value == "NOT_INITIALIZED" and len(node.children) == 1:
            node = node.children[0]

        # Could add the tokens from which the node
        # was created to the node (for debugging)
        return node

    def _initialize_node(self, search_field: str, unary_not: bool) -> Query:
        """Initialize a node."""
        node = Query(search_field=search_field, operator=True)
        if unary_not:
            node.value = Operators.NOT
        return node

    def _get_next_item(self, tokens: list) -> typing.Tuple[str, typing.Tuple[int, int]]:
        """Get the next item from the tokens."""
        return tokens.pop(0)

    def _handle_term(
        self,
        node: Query,
        next_item: str,
        search_field: str,
        pos: typing.Tuple[int, int],
    ) -> Query:
        """Handle term."""
        value = next_item.lstrip('"').rstrip('"')
        term_node = Query(
            value=value,
            operator=False,
            search_field=search_field,
            position=pos,
        )
        node.children.append(term_node)
        return node

    def _handle_near(
        self,
        node: Query,
        next_item: str,
        pos: typing.Tuple[int, int],
        current_operator: str,
    ) -> typing.Tuple[Query, str]:
        """Handle NEAR operator."""
        _, near_param = next_item.upper().split("/")
        node.near_param = int(near_param)  # type: ignore
        node.operator = True
        node.value = "NEAR"
        node.position = pos
        current_operator = "NEAR"
        return node, current_operator

    def _handle_and_or(
        self,
        node: Query,
        next_item: str,
        pos: typing.Tuple[int, int],
        current_operator: str,
    ) -> typing.Tuple[Query, str]:
        """Handle AND or OR operator."""
        if current_operator.upper() not in [next_item.upper(), ""]:
            raise ValueError(
                f"Invalid Syntax (combining {current_operator} with {next_item})"
            )
        node.operator = True
        node.value = next_item.upper()
        node.position = pos
        current_operator = next_item.upper()
        return node, current_operator

    def _handle_not(
        self,
        node: Query,
        tokens: list,
        search_field: str,
        current_operator: str,
    ) -> Query:
        """Handle NOT operator."""
        if current_operator.upper() not in [Operators.AND, ""]:
            raise ValueError(f"Invalid Syntax (combining {current_operator} with NOT)")
        node.children.append(self.parse_node(tokens, search_field, unary_not=True))
        return node

    def translate_search_fields(self, node: Query) -> None:
        """Translate search fields."""
        if not node.children:
            node.search_field = node.search_field.replace("AB=", "Abstract")
            return

        for child in node.children:
            self.translate_search_fields(child)

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        node = self.parse_node(self.tokens)
        # self.translate_search_fields(node)
        return node


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    def is_or_node(self, node_content: str) -> bool:
        """Node content is OR node"""
        return bool(re.match(r"^\(?#\d+( OR #\d+)+\)?$", node_content, re.IGNORECASE))

    def is_and_node(self, node_content: str) -> bool:
        """Node content is AND node"""
        return bool(re.match(r"^\(?#\d+( AND #\d+)+\)?$", node_content, re.IGNORECASE))

    def get_children(self, node_content: str) -> list:
        """Get the children of a node."""
        return re.findall(r"#\d+", node_content)

    def parse_list(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str
        for line in query_str.split("\n"):
            match = re.match(r"^(\d+).\s+(.*)$", line)
            if not match:
                raise ValueError(f"line not matching format: {line}")
            node_nr, node_content = match.groups()
            self.tokens[f"#{node_nr}"] = node_content

    def parse_term_node(self, term_str: str) -> Query:
        """Parse a term node."""
        node_parser = WOSParser(term_str)
        node_parser.tokenize()
        return node_parser.parse_node(node_parser.tokens)

    def print_term_token_types(self, token_content: str) -> str:
        """Override with method to parse and print term node types."""

        node_parser = WOSParser(token_content)
        node_parser.tokenize()
        return node_parser.get_token_types(node_parser.tokens)
