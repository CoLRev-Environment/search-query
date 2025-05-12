#!/usr/bin/env python3
"""Validator for search queries."""
from __future__ import annotations

import re
import typing

from search_query.constants import QueryErrorCode
from search_query.constants import TokenTypes
from search_query.constants_ebsco import VALID_FIELDS_REGEX
from search_query.linter_base import QueryStringLinter

if typing.TYPE_CHECKING:
    import search_query.parser_ebsco
    from search_query.query import Query


class EBSCOQueryStringLinter(QueryStringLinter):
    """Linter for EBSCO Query Strings"""

    UNSUPPORTED_SEARCH_FIELD_REGEX = r"\b(?!OR\b)\b(?!S\d+\b)[A-Z]{2}\b"

    VALID_TOKEN_SEQUENCES = {
        TokenTypes.FIELD: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.SEARCH_TERM: [
            TokenTypes.SEARCH_TERM,
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

    parser: search_query.parser_ebsco.EBSCOParser

    def __init__(self, parser: search_query.parser_ebsco.EBSCOParser):
        self.search_str = parser.query_str
        self.parser = parser
        super().__init__(parser=parser)

    def validate_tokens(self) -> None:
        """Pre-linting checks."""

        self.check_invalid_syntax()
        self.check_missing_tokens()
        self.check_quoted_search_terms()
        self.check_unknown_token_types()
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()
        self.check_invalid_characters_in_search_term("@&%$^~\\<>{}()[]#")
        self.check_unsupported_search_fields(valid_fields_regex=VALID_FIELDS_REGEX)

        self.check_token_ambiguity()
        self.check_search_field_general()

    def check_invalid_syntax(self) -> None:
        """Check for invalid syntax in the query string."""

        # Check for erroneous field syntax
        match = re.search(r"\[[A-Za-z]*\]", self.parser.query_str)
        if match:
            self.add_linter_message(
                QueryErrorCode.INVALID_SYNTAX,
                position=match.span(),
                details="EBSCOHOst fields must be before search terms "
                "and without brackets, e.g. AB robot or TI monitor. "
                f"'{match.group(0)}' is invalid.",
            )

    def check_token_ambiguity(self) -> None:
        """Check for ambiguous tokens in the query."""
        # Note: EBSCO-specific

        prev_token = None
        for i, token in enumerate(self.parser.tokens):
            match = re.match(r"^[A-Z]{2} ", token.value)
            if (
                token.type == TokenTypes.SEARCH_TERM
                and match
                and (prev_token is None or prev_token.type != TokenTypes.FIELD)
                and not self.parser.tokens[i + 1].startswith('"')
            ):
                details = (
                    f"The token '{token.value}' (at {token.position}) is ambiguous. "
                    + f"The {match.group()}could be a search field or a search term. "
                    + "To avoid confusion, please add quotes."
                )
                self.add_linter_message(
                    QueryErrorCode.TOKEN_AMBIGUITY,
                    position=(token.position[0], token.position[0] + 2),
                    details=details,
                )

            prev_token = token

    def check_search_field_general(self) -> None:
        """Check field 'Search Fields' in content."""

        if self.search_field_general != "":
            self.add_linter_message(QueryErrorCode.SEARCH_FIELD_EXTRACTED, position=())

    def check_invalid_token_sequences(self) -> None:
        """
        Check for invalid token sequences
        based on token type and the previous token type.
        """

        for i, token in enumerate(self.parser.tokens):
            # Check the last token
            if i == len(self.parser.tokens):
                if self.parser.tokens[i - 1].type in [
                    TokenTypes.PARENTHESIS_OPEN,
                    TokenTypes.LOGIC_OPERATOR,
                    TokenTypes.SEARCH_TERM,
                ]:
                    self.add_linter_message(
                        QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                        position=self.parser.tokens[i - 1].position,
                        details=f"Cannot end with {self.parser.tokens[i-1].type}",
                    )
                break

            token_type = token.type
            # Check the first token
            if i == 0:
                if token_type not in [
                    TokenTypes.SEARCH_TERM,
                    TokenTypes.FIELD,
                    TokenTypes.PARENTHESIS_OPEN,
                ]:
                    self.add_linter_message(
                        QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                        position=token.position,
                        details=f"Cannot start with {token_type}",
                    )
                continue

            prev_type = self.parser.tokens[i - 1].type

            if token_type not in self.VALID_TOKEN_SEQUENCES[prev_type]:
                if token_type == TokenTypes.FIELD:
                    details = "Invalid search field position"
                    position = token.position

                elif token_type == TokenTypes.LOGIC_OPERATOR:
                    details = "Invalid operator position"
                    position = token.position

                elif (
                    prev_type == TokenTypes.PARENTHESIS_OPEN
                    and token_type == TokenTypes.PARENTHESIS_CLOSED
                ):
                    details = "Empty parenthesis"
                    position = (
                        self.parser.tokens[i - 1].position[0],
                        token.position[1],
                    )
                elif token_type == TokenTypes.PARENTHESIS_OPEN and re.match(
                    r"^[a-z]{2}$", self.parser.tokens[i - 1].value
                ):
                    details = "Search field is not supported (must be upper case)"
                    position = self.parser.tokens[i - 1].position
                    self.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                        position=position,
                        details=details,
                    )
                    continue
                elif (
                    token_type and prev_type and prev_type != TokenTypes.LOGIC_OPERATOR
                ):
                    details = "Missing operator"
                    position = (
                        self.parser.tokens[i - 1].position[0],
                        token.position[1],
                    )

                else:
                    details = ""
                    position = (
                        token.position
                        if token_type
                        else self.parser.tokens[i - 1].position
                    )

                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    position=position,
                    details=details,
                )

    def validate_query_tree(self, query: Query) -> None:
        """
        Validate the query tree.
        This method is called after the query tree has been built.
        """
