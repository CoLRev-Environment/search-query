#!/usr/bin/env python3
"""WOS query parser."""
from __future__ import annotations

import re
import typing

import search_query.exception as search_query_exception
from search_query.constants import DB
from search_query.constants import DB_FIELD_TRANSLATION_MAP
from search_query.constants import Fields
from search_query.constants import Operators
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class WOSParser(QueryStringParser):
    """Parser for Web of Science queries."""

    FIELD_TRANSLATION_MAP = DB_FIELD_TRANSLATION_MAP[DB.WOS]

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

    def translate_search_fields(self, node: Query) -> None:
        """Translate search fields."""

        # Note: in the translation, we lose the position on purpose
        # (using str instead of SearchField)

        if not node.children:
            if not node.operator and not node.search_field:
                # TODO : TBD: should we raise an exception here?
                # or assume that "AllFields" was used as the default?
                raise search_query_exception.WOSSyntaxMissingSearchField(
                    # msg=f"Missing search field",
                    query_string=self.query_str,
                    pos=node.position or (0, 0),
                )

            # https://webofscience.help.clarivate.com/en-us/Content/wos-core-collection/woscc-search-field-tags.htm
            if not node.children and not node.operator and node.search_field:
                if str(node.search_field) in self.FIELD_TRANSLATION_MAP:
                    search_field_value = self.FIELD_TRANSLATION_MAP[
                        str(node.search_field)
                    ]
                    node.search_field = SearchField(search_field_value)
                elif str(node.search_field) == "MHX=":
                    replacement = {"MHX=": "SU="}
                    print(
                        f"Invalid search field: {node.search_field} "
                        + f"is deprecated (use {replacement[str(node.search_field)]})"
                    )
                    node.search_field = SearchField(Fields.RESEARCH_AREA)
                else:
                    raise search_query_exception.QuerySyntaxError(
                        msg=f"Invalid search field: {node.search_field}",
                        query_string=self.query_str,
                        pos=node.search_field.position or (0, 0),
                    )
                return

        for child in node.children:
            self.translate_search_fields(child)

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
        unary_not: bool = False,
    ) -> Query:
        """Parse a node from a list of tokens."""
        # SearchField
        node = self._initialize_node(search_field, unary_not)
        current_operator = ""
        expecting_operator = False
        parent_node = None  # for re-nesting OR/AND nodes

        while tokens:
            if unary_not and len(node.children) > 0:
                break
            next_item, pos = self._get_next_item(tokens)
            if self.is_search_field(next_item):
                search_field = SearchField(next_item, position=pos)
                next_item, pos = self._get_next_item(tokens)
            else:
                pass
            if next_item == ")":
                # Make sure we dont' read "()" (empty parentheses)
                assert len(node.children) > 0
                break

            if self.is_term(next_item):
                if str(search_field) == "":
                    raise search_query_exception.WOSInvalidFieldTag(
                        msg="WOS Search Error: No search field.",
                        query_string=self.query_str,
                        pos=pos,
                    )

                node = self._handle_term(node, next_item, search_field, pos)
                expecting_operator = True
                continue

            if next_item.upper() in [
                Operators.AND,
                Operators.OR,
            ] or next_item.upper().startswith(Operators.NEAR):
                assert expecting_operator
                # TODO : handle operator precedence if OR/AND are mixed
                if (
                    current_operator.upper() == Operators.OR
                    and next_item.upper() == Operators.AND
                ):
                    renested_node = node
                    node = Query(search_field=search_field, operator=True)
                    node.children.append(renested_node)
                    current_operator = ""

                if (
                    current_operator.upper() == Operators.AND
                    and next_item.upper() == Operators.OR
                ):
                    parent_node = node

                    tokens.insert(0, (next_item, pos))
                    prev_child = parent_node.children[-1]

                    node = Query(search_field=search_field, operator=True)
                    node.children.append(prev_child)
                    # Replace last child of parent_node with node
                    parent_node.children[-1] = node
                    current_operator = ""

                # TODO : NEAR can involve complex nodes (not just terms)
                # 10.1079_SEARCHRXIV.2023.00094.json
                if (
                    # current_operator.upper() in [Operators.AND, Operators.OR]
                    # and next_item.upper().startswith(Operators.NEAR)
                    next_item.upper().startswith(Operators.NEAR)
                ):
                    # raise Exception
                    prev_child = node.children[-1]

                    near_node = Query(search_field=search_field, operator=True)
                    _, near_param = next_item.upper().split("/")
                    near_node.near_param = int(near_param)  # type: ignore
                    near_node.value = Operators.NEAR

                    near_node.children.append(prev_child)
                    next_item, pos = self._get_next_item(tokens)

                    if next_item == "(":
                        near_node.children.append(
                            self.parse_query_tree(tokens, search_field)
                        )
                    else:
                        self._handle_term(near_node, next_item, search_field, pos)

                    # Replace last child of parent_node with node
                    node.children[-1] = near_node
                    current_operator = ""
                    continue

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

        if parent_node:
            node = parent_node

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
        value = next_item  # .lstrip('"').rstrip('"')
        term_node = Query(
            value=value,
            operator=False,
            search_field=search_field,
            position=pos,
        )
        node.children.append(term_node)
        return node

    # pylint: disable=duplicate-code
    def _handle_and_or(
        self,
        node: Query,
        next_item: str,
        pos: typing.Tuple[int, int],
        current_operator: str,
    ) -> typing.Tuple[Query, str]:
        """Handle AND or OR operator."""
        if current_operator.upper() not in [next_item.upper(), ""]:
            raise search_query_exception.QuerySyntaxError(
                msg=f"Attempt to combine {current_operator} with {next_item}",
                query_string=self.query_str,
                pos=pos,
            )
        node.operator = True
        node.position = pos
        if next_item.upper() in [Operators.AND, Operators.OR]:
            node.value = next_item.upper()
        elif next_item.upper().startswith(Operators.NEAR):
            _, near_param = next_item.upper().split("/")
            node.near_param = int(near_param)  # type: ignore
            node.value = Operators.NEAR
        else:
            raise search_query_exception.QuerySyntaxError(
                msg=f"Invalid operator: {next_item}",
                query_string=self.query_str,
                pos=pos,
            )

        current_operator = node.value
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

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        # print(self.get_token_types(self.tokens))
        node = self.parse_query_tree(self.tokens)
        self.translate_search_fields(node)
        return node


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"

    def __init__(self, query_list: str) -> None:
        super().__init__(query_list, WOSParser)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"
