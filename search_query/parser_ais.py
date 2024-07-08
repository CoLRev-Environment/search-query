#!/usr/bin/env python3
"""AIS eLibrary query parser."""
from __future__ import annotations

import re
import typing

import search_query.exception as search_query_exception
from search_query.constants import Fields
from search_query.constants import Operators
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class AISParser(QueryStringParser):
    """Parser for AIS eLibrary queries."""

    # Note: all fields: implicitly set as the search_field
    search_field_regex = (
        r"(abstract|subject|author|institution|title|document_type|"
        + r"publication_title|configured_field_t_issn)\:"
    )
    boolean_operators_regex = r"\b(AND|OR|NOT)\b"
    parentheses_regex = r"\(|\)"
    quoted_string_regex = r"\"[^\"]*\""
    string_regex = (
        r"\b(?!(?:AND|OR|NOT)\b)[\w\?\$-]+"
        + r"(?:\s+(?!(?:AND|OR|NOT)\b)[\w\?\$-]+)*\*?"
    )

    pattern = "|".join(
        [
            search_field_regex,
            boolean_operators_regex,
            parentheses_regex,
            quoted_string_regex,
            string_regex,
        ]
    )

    def get_non_tokenized(self) -> list:
        """Get the non-tokenized items (for debugging)"""
        non_tokenized = []
        cur_pos = 0
        for token in self.tokens:
            _, pos = token
            pos_start, pos_end = pos
            if pos_start > cur_pos:
                non_tokenized_content = self.query_str[cur_pos:pos_start]
                if non_tokenized_content != " ":
                    non_tokenized.append((non_tokenized_content, (cur_pos, pos_start)))
            cur_pos = pos_end
        if pos_end < len(self.query_str):
            non_tokenized.append(
                (
                    self.query_str[pos_end : len(self.query_str)],
                    (pos_end, len(self.query_str)),
                )
            )
        return non_tokenized

    def _validate_tokens(self) -> None:
        non_tokenized = self.get_non_tokenized()
        assert not non_tokenized, non_tokenized

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str.replace("”", '"').replace("“", '"')
        tokens = [
            (m.group(0), (m.start(), m.end()))
            for m in re.finditer(self.pattern, query_str, re.IGNORECASE)
        ]

        self.tokens = [(token.strip(), pos) for token, pos in tokens if token.strip()]

    def is_search_field(self, token: str) -> bool:
        return bool(re.search(f"^{self.search_field_regex}$", token))

    def is_operator(self, token: str) -> bool:
        """Token is operator"""
        return bool(re.match(r"^(AND|OR|NOT|NEAR/\d+)$", token, re.IGNORECASE))

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
        unary_not: bool = False,
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
                search_field = SearchField(next_item, position=pos)
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
                node.children.append(self.parse_query_tree(tokens, search_field))
                expecting_operator = True

        # Single-element parenthesis
        if node.value == "NOT_INITIALIZED" and len(node.children) == 1:
            node = node.children[0]

        # Could add the tokens from which the node
        # was created to the node (for debugging)
        return node

    def _initialize_node(
        self, search_field: typing.Optional[SearchField], unary_not: bool
    ) -> Query:
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
        search_field: typing.Optional[SearchField],
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
        search_field: typing.Optional[SearchField],
        current_operator: str,
    ) -> Query:
        """Handle NOT operator."""
        if current_operator.upper() not in [Operators.AND, ""]:
            raise ValueError(f"Invalid Syntax (combining {current_operator} with NOT)")
        node.children.append(
            self.parse_query_tree(tokens, search_field, unary_not=True)
        )
        return node

    def translate_search_fields(self, node: Query) -> None:
        """Translate search fields."""
        if not node.children:
            if str(node.search_field) == "title:":
                node.search_field = SearchField(Fields.TITLE)
            elif str(node.search_field) == "abstract:":
                node.search_field = SearchField(Fields.ABSTRACT)
            elif str(node.search_field) == "subject:":
                node.search_field = SearchField(Fields.TOPIC)
            else:
                raise search_query_exception.QuerySyntaxError(
                    msg=f"Invalid search field: {node.search_field}",
                    query_string=self.query_str,
                    pos=node.position or (0, 0),
                )

            return
        for child in node.children:
            self.translate_search_fields(child)

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        self._validate_tokens()
        node = self.parse_query_tree(self.tokens)
        self.translate_search_fields(node)
        return node
