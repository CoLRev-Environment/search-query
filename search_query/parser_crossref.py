#!/usr/bin/env python3
"""Crossref query parser."""
from __future__ import annotations

import re
import typing
from urllib.parse import unquote

import search_query.exception as search_query_exception
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class CrossrefParser(QueryStringParser):
    """Parser for Crossref queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.CROSSREF]

    pattern = r"(\w+)\?|([\w\.\+]+)|="

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        query_str = self.query_str
        assert query_str.startswith("https://api.crossref.org/")
        query_str = query_str[len("https://api.crossref.org/") :]

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
                raise search_query_exception.CrossrefSyntaxMissingSearchField(
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
                # elif str(node.search_field) == "MHX=":
                #     replacement = {"MHX=": "SU="}
                #     print(
                #         f"Invalid search field: {node.search_field} "
                #         + f"is deprecated (use {replacement[str(node.search_field)]})"
                #     )
                #     node.search_field = SearchField(Fields.RESEARCH_AREA)
                else:
                    raise search_query_exception.QuerySyntaxError(
                        msg=f"Invalid search field: {node.search_field}",
                        query_string=self.query_str,
                        pos=node.search_field.position or (0, 0),
                    )
                return

        for child in node.children:
            self.translate_search_fields(child)

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Parse a node from a list of tokens."""

        endpoint, _ = self._get_next_item(tokens)
        if endpoint not in ["works?", "journal"]:
            raise search_query_exception.QuerySyntaxError(
                msg=f"Invalid endpoint: {endpoint}",
                query_string=self.query_str,
                pos=(0, 0),
            )

        parent_node = Query(
            value=Operators.AND, search_field=search_field, operator=True
        )
        # SearchField
        while tokens:
            search_field_str, search_field_pos = self._get_next_item(tokens)
            if search_field_str in ["sort", "order"]:
                print("sort and order are not yet supported")
                _, _ = self._get_next_item(tokens)
                _, _ = self._get_next_item(tokens)
                if not tokens:
                    break
                print(tokens)
                continue
            _, _ = self._get_next_item(tokens)
            search_value, pos = self._get_next_item(tokens)
            search_value = unquote(search_value).replace("+", " ")

            node = Query(
                value=search_value,
                search_field=SearchField(search_field_str),
                position=pos,
            )
            parent_node.children.append(node)

        # if len(self.children) == !: unnest
        if len(parent_node.children) == 1:
            return parent_node.children[0]
        return parent_node

    def _get_next_item(self, tokens: list) -> typing.Tuple[str, typing.Tuple[int, int]]:
        """Get the next item from the tokens."""
        return tokens.pop(0)

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()

        node = self.parse_query_tree(self.tokens)
        print(node.to_string())
        self.translate_search_fields(node)

        # TODO : validate url with ISSN_REGEX, YEAR_SCOPE_REGEX
        # call at crossref_search_source._validate_api_params()

        return node
