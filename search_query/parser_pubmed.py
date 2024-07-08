#!/usr/bin/env python3
"""Pubmed query parser."""
from __future__ import annotations

import re
import typing

import search_query.exception as search_query_exception
from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import Syntax
from search_query.constants import SYNTAX_FIELD_TRANSLATION_MAP
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class PubmedParser(QueryStringParser):
    """Parser for Pubmed queries."""

    FIELD_TRANSLATION_MAP = SYNTAX_FIELD_TRANSLATION_MAP[Syntax.PUBMED]

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str.replace("”", '"').replace("“", '"')
        # query_str = f"({query_str})"
        pattern = (
            r"\[[A-Za-z:]+\]|\"[^\"]*\"|\bAND\b|\bOR\b|\bNOT\b|\(|\)|\b[\w-]+\b\*?"
        )
        tokens = [
            (m.group(0), (m.start(), m.end())) for m in re.finditer(pattern, query_str)
        ]
        self.tokens = [(token.strip(), pos) for token, pos in tokens if token.strip()]

    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return bool(re.search(r"\[[A-Za-z:]+\]", token))

    def get_type(self, token: str) -> str:
        """Get the token type"""
        if self.is_search_field(token):
            return "search_field"
        if self.is_parenthesis(token):
            return "parenthesis"
        if self.is_operator(token):
            return "operator"
        if self.is_term(token):
            return "term"
        return "NOT_MATCHED"

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
        unary_not: bool = False,
    ) -> Query:
        """Parse a node from a list of tokens."""
        # Assume that expressions start with "("
        # (we can always add surrounding parentheses)

        node = Query(search_field=search_field, operator=True)
        if unary_not:
            node.value = "NOT"

        current_operator = ""
        expecting_operator = False
        while tokens:
            if unary_not and len(node.children) > 0:
                break
            next_item, pos = tokens.pop(0)
            if next_item == ")":
                # Make sure we dont' read "()"
                assert len(node.children) > 0
                break

            if self.is_term(next_item):
                value = next_item.lstrip('"').rstrip('"')
                term_node = Query(
                    value=value,
                    operator=False,
                    search_field=search_field,  # .strip()
                    position=pos,
                )

                next_token, _ = tokens[0]
                if self.is_search_field(next_token):
                    next_item, pos = tokens.pop(0)
                    search_field = SearchField(next_item.strip(), position=pos)
                    term_node.search_field = search_field

                node.children.append(term_node)
                expecting_operator = True
                continue

            if next_item in [Operators.AND, Operators.OR]:
                assert expecting_operator, tokens
                if current_operator not in [next_item, ""]:
                    raise search_query_exception.QuerySyntaxError(
                        msg=f"Attempt to combine {current_operator} with {next_item}",
                        query_string=self.query_str,
                        pos=pos,
                    )

                node.operator = True
                node.value = next_item
                node.position = pos
                expecting_operator = False
                current_operator = next_item
                continue

            if next_item == Operators.NOT:
                assert expecting_operator, tokens
                if current_operator not in [Operators.AND, ""]:
                    raise ValueError(
                        f"Invalid Syntax (combining {current_operator} with NOT)"
                    )
                node.children.append(
                    self.parse_query_tree(tokens, search_field, unary_not=True)
                )
                continue

            if next_item == "(":
                node.children.append(self.parse_query_tree(tokens, search_field))
                # if tokens:
                #     assert tokens.pop(0) == ')', tokens
                expecting_operator = True

        # Single-element parenthesis
        if node.value == "NOT_INITIALIZED" and len(node.children) == 1:
            node = node.children[0]

        # Could add the tokens from which the node
        # was created to the node (for debugging)
        return node

    def translate_search_fields(self, node: Query) -> None:
        """Translate search fields."""

        if not node.children:
            if not node.search_field:
                return

            # Search fields are not case sensitive
            search_field_lc = node.search_field.value.lower()

            if search_field_lc in self.FIELD_TRANSLATION_MAP:
                node.search_field = SearchField(
                    self.FIELD_TRANSLATION_MAP[search_field_lc]
                )

            # Deprecated field
            elif search_field_lc == "[mesh]":
                node.search_field = SearchField(Fields.MESH)

            # TODO : move to constants...
            # INSTEAD: translate by adding sibling-nodes
            # or even creating a new parent OR?!
            elif search_field_lc in ["[tiab]"]:
                node.search_field = SearchField("tiab")
                node.children.insert(
                    0, Query(node.value, search_field=SearchField("ti"))
                )
                node.children.insert(
                    1, Query(node.value, search_field=SearchField("ab"))
                )
                node.value = "OR"
                node.operator = True
                node.search_field = None

            elif search_field_lc in ["[mj]"]:
                replacement = {"[mj]": "[majr]"}
                raise search_query_exception.QuerySyntaxError(
                    msg=f"Invalid search field: {node.search_field} "
                    + f"is deprecated (use {replacement[str(node.search_field)]})",
                    query_string=self.query_str,
                    pos=node.position or (0, 0),
                )
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
        node = self.parse_query_tree(self.tokens)
        self.translate_search_fields(node)
        return node
