#!/usr/bin/env python3
"""Cinahl query parser."""
from __future__ import annotations

import re

from search_query.parser_base import QueryListParser
from search_query.query import Query


class CINAHLParser(QueryListParser):
    """Parser for CINAHL queries."""

    def is_or_node(self, node_content: str) -> bool:
        """Node content is OR node"""
        return bool(re.match(r"^\(?S\d+( OR S\d+)+\)?$", node_content))

    def is_and_node(self, node_content: str) -> bool:
        """Node content is AND node"""
        return bool(re.match(r"^\(?S\d+( AND S\d+)+\)?$", node_content))

    def is_node_identifier(self, node_content: str) -> bool:
        """Node content is node identifier"""
        return bool(re.match(r"^S\d+$", node_content))

    def parse_list(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str
        for line in query_str.split("\n"):
            match = re.match(r"^(\d+).\s+(.*)$", line)
            if not match:
                raise ValueError(f"line not matching format: {line}")
            node_nr, node_content = match.groups()
            self.tokens[f"S{node_nr}"] = node_content

    def parse_term_node(self, term_str: str) -> Query:
        """Parse a term node."""

        return Query(value=term_str, operator=False)

    def get_children(self, node_content: str) -> list:
        """Get the children of a node."""
        return re.findall(r"S\d+", node_content)

    def translate_search_fields(self, node: Query) -> None:
        """Translate search fields."""

        if not node.children:
            raise NotImplementedError

        for child in node.children:
            self.translate_search_fields(child)
