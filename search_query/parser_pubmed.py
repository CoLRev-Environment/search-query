#!/usr/bin/env python3
"""Pubmed query parser."""
from __future__ import annotations

import re
import typing

import search_query.exception as search_query_exception
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import Fields
from search_query.constants import Operators
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class PubmedParser(QueryStringParser):
    """Parser for Pubmed queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.PUBMED]

    search_field_regex = r"\[[A-Za-z: \/0-9~]+\]"
    boolean_operators_regex = r"\b(AND|OR|NOT)\b"
    parentheses_regex = r"\(|\)"
    quoted_string_regex = r"\"[^\"]*\""
    date_range_regex = r"\b\d{4}:\d{4}\b"

    # proximity_search_regex = r"\bNEAR\/\d+"
    string_regex = r"\b[\w-]+\b\*?"

    pattern = "|".join(
        [
            search_field_regex,
            date_range_regex,  # Must be before string_regex
            boolean_operators_regex,
            # proximity_search_regex,
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
            for m in re.finditer(self.pattern, query_str)
        ]
        self.tokens = [(token.strip(), pos) for token, pos in tokens if token.strip()]
        self.combine_subsequent_terms()

    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return bool(re.search(self.search_field_regex, token))

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

    # pylint: disable=too-many-branches
    def parse_query_tree(
        self,
        tokens: list,
        search_field: SearchField = SearchField("[all]"),
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
                if not tokens:
                    node.children.append(term_node)
                    break
                next_token, _ = tokens[0]
                if self.is_search_field(next_token):
                    next_item, pos = tokens.pop(0)
                    search_field = SearchField(next_item.strip(), position=pos)
                    term_node.search_field = search_field

                node.children.append(term_node)
                expecting_operator = True
                continue

            if next_item.upper() in [Operators.AND, Operators.OR]:
                assert expecting_operator, tokens
                if current_operator not in [next_item, ""]:
                    raise search_query_exception.QuerySyntaxError(
                        msg=f"Attempt to combine {current_operator} with {next_item}",
                        query_string=self.query_str,
                        pos=pos,
                    )

                node.operator = True
                node.value = next_item.upper()
                node.position = pos
                expecting_operator = False
                current_operator = next_item
                continue

            if next_item.upper() == Operators.NOT:
                assert expecting_operator, tokens
                if current_operator not in [Operators.AND, ""]:
                    raise ValueError(
                        f"Invalid Syntax (combining {current_operator} with NOT)"
                    )
                if current_operator == "":
                    current_operator = Operators.AND
                    node.value = "AND"
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

    # pylint: disable=too-many-branches
    def translate_search_fields(self, node: Query) -> None:
        """Translate search fields."""

        if not node.children:
            if not node.search_field:
                return

            # Search fields are not case sensitive
            search_field_lc = node.search_field.value.lower()
            # left and right spaces between parentheses are removed
            search_field_lc = re.sub(r"\[\s+", "[", search_field_lc)
            search_field_lc = re.sub(r"\s+\]", "]", search_field_lc)

            if search_field_lc in self.FIELD_TRANSLATION_MAP:
                node.search_field = SearchField(
                    self.FIELD_TRANSLATION_MAP[search_field_lc]
                )
            # Non-default fields
            elif search_field_lc in ["[mesh]", "[mesh terms]"]:
                node.search_field = SearchField(Fields.MESH)
            elif search_field_lc == "[title]":
                node.search_field = SearchField(Fields.TITLE)
            elif search_field_lc == "[abstract]":
                node.search_field = SearchField(Fields.ABSTRACT)
            elif search_field_lc == "[filter]":
                node.search_field = SearchField(Fields.SUBSET)
            elif search_field_lc == "[language]":
                node.search_field = SearchField(Fields.LANGUAGE)
            elif search_field_lc == "[all fields]":
                node.search_field = SearchField(Fields.ALL)
            # TODO : convert to standard format!!
            elif search_field_lc == "[pdat]":
                node.search_field = SearchField(Fields.YEAR)
            elif search_field_lc == "[text word]":
                node.search_field = SearchField(Fields.TEXT_WORDS)
            elif search_field_lc == "[supplementary concept]":
                node.search_field = SearchField(Fields.SUPPLEMENTARY_CONCEPT)
            elif search_field_lc in ["[subheading]", "[mesh subheading]"]:
                node.search_field = SearchField(Fields.SUBHEADING)
            elif search_field_lc == "[mesh terms:noexp]":
                node.search_field = SearchField(Fields.MESH_NO_EXP)
            elif search_field_lc == "[publication type]":
                node.search_field = SearchField(Fields.PUBLICATION_TYPE)
            elif search_field_lc == "[pharmacological action]":
                node.search_field = SearchField(Fields.PHARMACOLOGICAL_ACTION)
            elif search_field_lc == "[mj]":
                node.search_field = SearchField(Fields.MESH)
            elif search_field_lc == "[journal]":
                node.search_field = SearchField(Fields.JOURNAL)

            # TODO : move to constants...
            # INSTEAD: translate by adding sibling-nodes
            # or even creating a new parent OR?!
            elif search_field_lc in ["[tiab]", "[title/abstract]"]:
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

            else:
                raise search_query_exception.QuerySyntaxError(
                    msg=f"Invalid search field: {node.search_field}",
                    query_string=self.query_str,
                    pos=node.search_field.position or (0, 0),
                )

            return

        for child in node.children:
            self.translate_search_fields(child)

    def lint(self) -> list:
        """Lint the query string."""
        messages: typing.List[dict] = []

        # TODO / TBD: should we raise an error during parse()
        # and append messages during lint()?

        # Check the query_string
        self.tokenize()
        # Check the tokens
        node = self.parse_query_tree(self.tokens)
        # Check the query tree
        self.translate_search_fields(node)
        # Check the search fields
        return messages

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        node = self.parse_query_tree(self.tokens)
        self.translate_search_fields(node)
        return node


class PubmedListParser(QueryListParser):
    """Parser for Pubmed list queries."""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"

    def __init__(self, query_list: str) -> None:
        super().__init__(query_list, PubmedParser)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"
