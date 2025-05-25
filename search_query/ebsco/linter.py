#!/usr/bin/env python3
"""Validator for search queries."""
from __future__ import annotations

import re
import typing

from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.ebsco.constants import syntax_str_to_generic_search_field_set
from search_query.ebsco.constants import VALID_FIELDS_REGEX
from search_query.linter_base import QueryStringLinter

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


class EBSCOQueryStringLinter(QueryStringLinter):
    """Linter for EBSCO Query Strings"""

    UNSUPPORTED_SEARCH_FIELD_REGEX = r"\b(?!OR\b)\b(?!S\d+\b)[A-Z]{2}\b"

    PLATFORM: PLATFORM = PLATFORM.EBSCO
    VALID_FIELDS_REGEX = VALID_FIELDS_REGEX

    VALID_TOKEN_SEQUENCES = {
        TokenTypes.FIELD: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.SEARCH_TERM: [
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PROXIMITY_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.LOGIC_OPERATOR: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.FIELD,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.PROXIMITY_OPERATOR: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
            TokenTypes.FIELD,
        ],
        TokenTypes.PARENTHESIS_OPEN: [
            TokenTypes.FIELD,
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.PARENTHESIS_CLOSED: [
            TokenTypes.PARENTHESIS_CLOSED,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PROXIMITY_OPERATOR,
        ],
    }

    def __init__(self, query_str: str = "") -> None:
        super().__init__(query_str=query_str)

    def validate_tokens(
        self,
        *,
        tokens: typing.List[Token],
        query_str: str,
        search_field_general: str = "",
    ) -> typing.List[Token]:
        """Pre-linting checks."""
        self.tokens = tokens
        self.query_str = query_str
        self.search_field_general = search_field_general

        self.check_invalid_syntax()
        self.check_missing_tokens()
        self.check_unknown_token_types()
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()

        self.check_search_field_general()
        return self.tokens

    def get_precedence(self, token: str) -> int:
        """Returns operator precedence for logical and proximity operators."""

        if token.startswith("N"):
            return self.OPERATOR_PRECEDENCE["NEAR"]
        if token.startswith("W"):
            return self.OPERATOR_PRECEDENCE["WITHIN"]
        if token in self.OPERATOR_PRECEDENCE:
            return self.OPERATOR_PRECEDENCE[token]
        return -1  # Not an operator

    def syntax_str_to_generic_search_field_set(self, field_value: str) -> set:
        return syntax_str_to_generic_search_field_set(field_value)

    def check_invalid_syntax(self) -> None:
        """Check for invalid syntax in the query string."""

        # Check for erroneous field syntax
        match = re.search(r"\[[A-Za-z]*\]", self.query_str)
        if match:
            self.add_linter_message(
                QueryErrorCode.INVALID_SYNTAX,
                positions=[match.span()],
                details="EBSCOHOst fields must be before search terms "
                "and without brackets, e.g. AB robot or TI monitor. "
                f"'{match.group(0)}' is invalid.",
            )

    def check_search_field_general(self) -> None:
        """Check field 'Search Fields' in content."""

        if self.search_field_general != "":
            self.add_linter_message(QueryErrorCode.SEARCH_FIELD_EXTRACTED, positions=[])

    def check_invalid_token_sequences(self) -> None:
        """
        Check for invalid token sequences
        based on token type and the previous token type.
        """

        # Check the first token
        if self.tokens[0].type not in [
            TokenTypes.SEARCH_TERM,
            TokenTypes.FIELD,
            TokenTypes.PARENTHESIS_OPEN,
        ]:
            self.add_linter_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                positions=[self.tokens[0].position],
                details=f"Cannot start with {self.tokens[0].type.value}",
            )

        for i, token in enumerate(self.tokens):
            if i == 0:
                continue

            token_type = token.type
            prev_type = self.tokens[i - 1].type

            if token_type not in self.VALID_TOKEN_SEQUENCES[prev_type]:
                details = ""
                positions = [
                    (token.position if token_type else self.tokens[i - 1].position)
                ]
                if token_type == TokenTypes.FIELD:
                    details = "Invalid search field position"
                    positions = [token.position]

                elif token_type == TokenTypes.LOGIC_OPERATOR:
                    details = "Invalid operator position"
                    positions = [token.position]

                elif (
                    prev_type == TokenTypes.PARENTHESIS_OPEN
                    and token_type == TokenTypes.PARENTHESIS_CLOSED
                ):
                    details = "Empty parenthesis"
                    positions = [
                        (
                            self.tokens[i - 1].position[0],
                            token.position[1],
                        )
                    ]
                elif token_type == TokenTypes.PARENTHESIS_OPEN and re.match(
                    r"^[a-z]{2}$", self.tokens[i - 1].value
                ):
                    details = "Search field is not supported (must be upper case)"
                    positions = [self.tokens[i - 1].position]
                    self.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                        positions=positions,
                        details=details,
                    )
                    continue
                elif (
                    token_type and prev_type and prev_type != TokenTypes.LOGIC_OPERATOR
                ):
                    details = "Missing operator between terms"
                    positions = [
                        (
                            self.tokens[i - 1].position[0],
                            token.position[1],
                        )
                    ]

                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    positions=positions,
                    details=details,
                )

        # Check the last token
        if self.tokens[-1].type in [
            TokenTypes.PARENTHESIS_OPEN,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.FIELD,
        ]:
            self.add_linter_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                positions=[self.tokens[-1].position],
                details=f"Cannot end with {self.tokens[-1].type.value}",
            )

    def validate_query_tree(self, query: Query) -> None:
        """
        Validate the query tree.
        This method is called after the query tree has been built.
        """

        self.check_unbalanced_quotes_in_terms(query)
        self.check_operator_capitalization_query(query)
        self.check_invalid_characters_in_search_term_query(query, "@&%$^~\\<>{}()[]#")
        self.check_unsupported_search_fields_in_query(query)

        term_field_query = self.get_query_with_fields_at_terms(query)
        self._check_date_filters_in_subquery(term_field_query)
        self._check_journal_filters_in_subquery(term_field_query)
        self._check_redundant_terms(term_field_query)
