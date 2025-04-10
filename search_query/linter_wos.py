#!/usr/bin/env python3
"""Web-of-Science query linter."""
import re
import typing

from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.constants import WOSSearchFieldList

if typing.TYPE_CHECKING:
    import search_query.parser_wos


class QueryLinter:
    """Linter for wos query"""

    language_list = [
        "LA=",
        "Languages",
        "la=",
        "language=",
        "la",
        "language",
        "LA",
        "LANGUAGE",
    ]
    WILDCARD_CHARS = ["?", "$", "*"]

    def __init__(self, parser: "search_query.parser_wos.WOSParser"):
        self.search_str = parser.query_str
        self.parser = parser

    def pre_linting(self) -> None:
        """Performs a pre-linting"""

        self.check_search_fields_from_json()
        self.check_unknown_token_types()
        self.check_operator_capitalization()
        self.check_implicit_near()
        self.check_year_format()
        self.check_fields()
        self.check_order_of_tokens()

        index = 0
        year_search_field_detected = False
        count_search_fields = 0
        while index < len(self.parser.tokens) - 1:
            token = self.parser.tokens[index]

            if "NEAR" in token.value:
                self.check_near_distance_in_range(index=index)

            if re.match(self.parser.YEAR_REGEX, token.value):
                year_search_field_detected = True

            if re.match(self.parser.SEARCH_FIELD_REGEX, token.value):
                count_search_fields += 1

            self.check_wildcards(token=token)

            index += 1

        self.check_unsupported_wildcards()

        self.handle_multiple_same_level_operators(tokens=self.parser.tokens, index=0)

        if year_search_field_detected and count_search_fields < 2:
            # Year detected without other search fields
            self.parser.add_linter_message(
                QueryErrorCode.YEAR_WITHOUT_SEARCH_FIELD,
                pos=token.position,
            )

        self.check_unmatched_parentheses()

    def check_search_fields_from_json(
        self,
    ) -> None:
        """Check if the search field is in the list of search fields from JSON."""

        for index, token in enumerate(self.parser.tokens):
            if token.type not in [TokenTypes.FIELD, TokenTypes.PARENTHESIS_OPEN]:
                if self.parser.search_field_general == "":
                    self.parser.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_MISSING,
                        pos=(-1, -1),
                    )
                break

            if token.type == TokenTypes.FIELD:
                if index == 0 and self.parser.search_field_general != "":
                    if token.value != self.parser.search_field_general:
                        self.parser.add_linter_message(
                            QueryErrorCode.SEARCH_FIELD_CONTRADICTION,
                            pos=token.position,
                        )
                    else:
                        # Note : in basic search, when starting the query with a field,
                        # WOS raises a syntax error.
                        self.parser.add_linter_message(
                            QueryErrorCode.SEARCH_FIELD_REDUNDANT,
                            pos=token.position,
                        )

                # break: only consider the first FIELD
                # (which may come after parentheses)
                break

    def check_fields(self) -> None:
        """Check for the correct format of fields."""
        valid_fields = set().union(*WOSSearchFieldList.search_field_dict.values())
        for token in self.parser.tokens:
            if token.type == TokenTypes.FIELD:
                if token.value not in valid_fields:
                    self.parser.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                        pos=token.position,
                    )

    def check_unknown_token_types(self) -> None:
        """Check for unknown token types."""
        for token in self.parser.tokens:
            if token.type == TokenTypes.UNKNOWN:
                self.parser.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED, token.position
                )

    def check_operator_capitalization(self) -> None:
        """Check if operators are capitalized."""
        for token in self.parser.tokens:
            if re.match(self.parser.OPERATOR_REGEX, token.value):
                if token.value != token.value.upper():
                    self.parser.add_linter_message(
                        QueryErrorCode.OPERATOR_CAPITALIZATION,
                        pos=token.position,
                    )
                    token.value = token.value.upper()

    def check_implicit_near(self) -> None:
        """Check for implicit NEAR operator."""
        for token in self.parser.tokens:
            if token.value == "NEAR":
                self.parser.add_linter_message(
                    QueryErrorCode.IMPLICIT_NEAR_VALUE,
                    pos=token.position,
                )
                token.value = "NEAR/15"

    def check_year_format(self) -> None:
        """Check for the correct format of year."""
        for index, token in enumerate(self.parser.tokens):
            if token.value in WOSSearchFieldList.year_published_list:
                year_token = self.parser.tokens[index + 1]

                if any(char in year_token.value for char in ["*", "?", "$"]):
                    self.parser.add_linter_message(
                        QueryErrorCode.WILDCARD_IN_YEAR,
                        pos=year_token.position,
                    )

                # Check if the yearspan is not more than 5 years
                if len(year_token.value) > 4:
                    if int(year_token.value[5:9]) - int(year_token.value[0:4]) > 5:
                        # Change the year span to five years
                        year_token.value = (
                            str(int(year_token.value[5:9]) - 5)
                            + "-"
                            + year_token.value[5:9]
                        )

                        self.parser.add_linter_message(
                            QueryErrorCode.YEAR_SPAN_VIOLATION, pos=year_token.position
                        )

    def check_unmatched_parentheses(self) -> None:
        """Check for unmatched parentheses in the query."""
        stack = []
        for i, char in enumerate(self.search_str):
            if char == "(":
                stack.append(i)
            elif char == ")":
                if stack:
                    stack.pop()
                else:
                    self.parser.add_linter_message(
                        QueryErrorCode.UNMATCHED_CLOSING_PARENTHESIS,
                        pos=(i, i + 1),
                    )

        for unmatched_index in stack:
            self.parser.add_linter_message(
                QueryErrorCode.UNMATCHED_OPENING_PARENTHESIS,
                pos=(unmatched_index, unmatched_index + 1),
            )

    def check_order_of_tokens(self) -> None:
        """Check for the correct order of tokens in the query."""

        valid_transitions = {
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

        tokens = self.parser.tokens

        for index in range(len(tokens) - 1):
            token = tokens[index]
            next_token = tokens[index + 1]

            # Skip known exceptions like NEAR proximity modifier (custom rule)
            if (
                token.type == TokenTypes.SEARCH_TERM
                and next_token.value == "("
                and index > 0
                and tokens[index - 1].value.upper() == "NEAR"
            ):
                continue

            # Allow known languages after parenthesis (custom rule)
            if token.value == ")" and next_token.value in self.language_list:
                continue

            # Two operators in a row
            if token.is_operator() and next_token.is_operator():
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE_TWO_OPERATORS,
                    pos=next_token.position,
                )
                continue

            # Two search fields in a row
            if token.type == TokenTypes.FIELD and next_token.type == TokenTypes.FIELD:
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE_TWO_SEARCH_FIELDS,
                    pos=next_token.position,
                )
                continue

            # Check transition
            allowed_next_types = valid_transitions.get(token.type, [])
            if next_token.type not in allowed_next_types:
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    pos=next_token.position,
                )

    def check_near_distance_in_range(self, index: int) -> None:
        """Check for NEAR with a specified distance out of range."""
        near_distance = re.findall(r"\d{1,2}", self.parser.tokens[index].value)
        if near_distance and int(near_distance[0]) > 15:
            self.parser.add_linter_message(
                QueryErrorCode.NEAR_DISTANCE_TOO_LARGE,
                pos=self.parser.tokens[index].position,
            )

    def check_unsupported_wildcards(self) -> None:
        """Check for unsupported characters in the search string."""

        # Web of Science does not support "!"
        for match in re.finditer(r"\!+", self.search_str):
            self.parser.add_linter_message(
                QueryErrorCode.WILDCARD_UNSUPPORTED,
                pos=(match.start(), match.end()),
            )

    def check_wildcards(self, token: Token) -> None:
        """Check for the usage of wildcards in the search string."""

        token_value = token.value.replace('"', "")

        # Implement constrains from Web of Science for Wildcards
        for index, charachter in enumerate(token_value):
            if charachter in self.WILDCARD_CHARS:
                # Check if wildcard is left or right-handed or standalone
                if index == 0 and len(token_value) == 1:
                    self.parser.add_linter_message(
                        QueryErrorCode.WILDCARD_STANDALONE,
                        pos=token.position,
                    )

                elif len(token_value) == index + 1:
                    # Right-hand wildcard
                    self.check_unsupported_right_hand_wildcards(
                        token=token, index=index
                    )

                elif index == 0 and len(token_value) > 1:
                    # Left-hand wildcard
                    self.check_format_left_hand_wildcards(token=token)

                else:
                    # Wildcard in the middle of the term
                    if token_value[index - 1] in ["/", "@", "#", ".", ":", ";", "!"]:
                        self.parser.add_linter_message(
                            QueryErrorCode.WILDCARD_AFTER_SPECIAL_CHAR,
                            pos=token.position,
                        )

    def check_unsupported_right_hand_wildcards(self, token: Token, index: int) -> None:
        """Check for unsupported right-hand wildcards in the search string."""

        if token.value[index - 1] in ["/", "@", "#", ".", ":", ";", "!"]:
            self.parser.add_linter_message(
                QueryErrorCode.WILDCARD_AFTER_SPECIAL_CHAR,
                pos=token.position,
            )

        if len(token.value) < 4:
            self.parser.add_linter_message(
                QueryErrorCode.WILDCARD_RIGHT_SHORT_LENGTH,
                pos=token.position,
            )

    def check_format_left_hand_wildcards(self, token: Token) -> None:
        """Check for wrong usage among left-hand wildcards in the search string."""

        if len(token.value) < 4:
            self.parser.add_linter_message(
                QueryErrorCode.WILDCARD_LEFT_SHORT_LENGTH,
                pos=token.position,
            )

    def check_issn_isbn_format(self, token: Token) -> None:
        """Check for the correct format of ISSN and ISBN."""
        token_vale = token.value.replace('"', "")
        if not re.match(self.parser.ISSN_REGEX, token_vale) and not re.match(
            self.parser.ISBN_REGEX, token_vale
        ):
            # Add messages to self.linter_messages
            self.parser.add_linter_message(
                QueryErrorCode.ISBN_FORMAT_INVALID,
                pos=token.position,
            )

    def check_doi_format(self, token: Token) -> None:
        """Check for the correct format of DOI."""
        token_value = token.value.replace('"', "").upper()
        if not re.match(self.parser.DOI_REGEX, token_value):
            # Add messages to self.linter_messages
            self.parser.add_linter_message(
                QueryErrorCode.DOI_FORMAT_INVALID,
                pos=token.position,
            )

    def handle_multiple_same_level_operators(self, tokens: list, index: int) -> int:
        """Handle multiple same level operators."""
        # This function introduces additional parantheses to the query tree
        # based on the precedence of the operators.
        # Precedence: NEAR > SAME > NOT > AND > OR
        operator_list: typing.List[str] = []
        clear_list = False
        while index < len(tokens):
            token = tokens[index]

            if token.value == "(":
                index = self.handle_multiple_same_level_operators(
                    tokens=tokens, index=index + 1
                )

            if token.value == ")":
                return index

            # Operator change
            if (
                operator_list
                and re.match(self.parser.OPERATOR_REGEX, token.value.upper())
                and token.value.upper() not in operator_list
                and token.value.upper() != "NOT"
            ):
                self.parser.add_linter_message(
                    QueryErrorCode.IMPLICIT_PRECEDENCE,
                    pos=token.position,
                )

                clear_list = True

            # Clear the operator list after inserting parentheses
            if clear_list:
                operator_list.clear()
                clear_list = False

            if (
                token.value.upper() in ["NEAR", "AND", "OR", "NOT"]
                or "NEAR" in token.value.upper()
            ):
                operator_list.append(token.value.upper())
            index += 1
        return index
