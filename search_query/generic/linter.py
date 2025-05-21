#!/usr/bin/env python3
"""Linter for generic queries."""
import re
import typing

from search_query.constants import Fields
from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.linter_base import QueryStringLinter

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


class GenericLinter(QueryStringLinter):
    """Linter for Generic Query Strings"""

    PRECEDENCE = {
        "NEAR": 3,
        "WITHIN": 3,
        "NOT": 2,
        "AND": 1,
        "OR": 0,
    }
    PLATFORM: PLATFORM = PLATFORM.GENERIC

    # Extract unique string values
    field_codes = {
        v
        for k, v in vars(Fields).items()
        if not k.startswith("__") and isinstance(v, str)
    }

    VALID_FIELDS_REGEX = re.compile(r"\b(?:" + "|".join(sorted(field_codes)) + r")\b")

    # VALID_TOKEN_SEQUENCES = {
    #     TokenTypes.FIELD: [
    #         TokenTypes.SEARCH_TERM,
    #         TokenTypes.PARENTHESIS_OPEN,
    #     ],
    #     TokenTypes.SEARCH_TERM: [
    #         TokenTypes.SEARCH_TERM,
    #         TokenTypes.LOGIC_OPERATOR,
    #         TokenTypes.PROXIMITY_OPERATOR,
    #         TokenTypes.PARENTHESIS_CLOSED,
    #     ],
    #     TokenTypes.LOGIC_OPERATOR: [
    #         TokenTypes.SEARCH_TERM,
    #         TokenTypes.FIELD,
    #         TokenTypes.PARENTHESIS_OPEN,
    #     ],
    #     TokenTypes.PROXIMITY_OPERATOR: [
    #         TokenTypes.SEARCH_TERM,
    #         TokenTypes.PARENTHESIS_OPEN,
    #         TokenTypes.FIELD,
    #     ],
    #     TokenTypes.PARENTHESIS_OPEN: [
    #         TokenTypes.FIELD,
    #         TokenTypes.SEARCH_TERM,
    #         TokenTypes.PARENTHESIS_OPEN,
    #     ],
    #     TokenTypes.PARENTHESIS_CLOSED: [
    #         TokenTypes.PARENTHESIS_CLOSED,
    #         TokenTypes.LOGIC_OPERATOR,
    #         TokenTypes.PROXIMITY_OPERATOR,
    #     ],
    # }

    def __init__(self, query_str: str = "") -> None:
        super().__init__(query_str=query_str)

    def syntax_str_to_generic_search_field_set(self, field_value: str) -> set:
        """Translate a search field"""
        return {field_value}

    def validate_tokens(
        self,
        *,
        tokens: typing.List[Token],
        query_str: str,
        search_field_general: str = "",
    ) -> typing.List[Token]:
        """Performs a pre-linting"""

        self.tokens = tokens
        self.query_str = query_str
        self.search_field_general = search_field_general

        # Currently doing nothing
        return self.tokens

    def validate_query_tree(self, query: "Query") -> None:
        """
        Validate the query tree.
        This method is called after the query tree has been built.
        """

        self.check_unsupported_search_fields_in_query(query)
