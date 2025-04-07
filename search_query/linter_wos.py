#!/usr/bin/env python3
"""Web-of-Science query linter."""
import re
import typing

from search_query.constants import QueryErrorCode
from search_query.constants import Token

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

        if len(self.parser.tokens) < 2:
            if '"' in self.parser.tokens[0][0]:
                # TODO : non-fatal error: remove quotes from tokens
                self.parser.add_linter_message(
                    QueryErrorCode.QUERY_IN_QUOTES,
                    pos=self.parser.tokens[0][1],
                )

        if self.parser.tokens[0][0] in [
            "Web of Science",
            "wos",
            "WoS",
            "WOS",
            "WOS:",
            "WoS:",
            "WOS=",
            "WoS=",
        ]:
            self.parser.add_linter_message(
                QueryErrorCode.QUERY_STARTS_WITH_PLATFORM_IDENTIFIER,
                pos=self.parser.tokens[0][1],
            )
            # TODO : non-fatal error: remove identifier from tokens

        self.check_order_of_tokens()

        index = 0
        year_search_field_detected = False
        count_search_fields = 0
        while index < len(self.parser.tokens) - 1:
            token = self.parser.tokens[index]

            if "NEAR" in token:
                self.check_near_distance_in_range(index=index)

            if re.match(self.parser.YEAR_REGEX, token):
                year_search_field_detected = True

            if re.match(self.parser.SEARCH_FIELD_REGEX, token):
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

        index = 0
        while index < len(self.parser.tokens) - 1:
            token = self.parser.tokens[index]
            next_token = self.parser.tokens[index + 1]

            # Check for two operators in a row
            if re.match(self.parser.OPERATOR_REGEX, token.value) and re.match(
                self.parser.OPERATOR_REGEX, next_token.value
            ):
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE_TWO_OPERATORS,
                    pos=next_token.position,
                )

            # Check for two search fields in a row
            if re.match(self.parser.SEARCH_FIELD_REGEX, token.value) and re.match(
                self.parser.SEARCH_FIELD_REGEX, next_token.value
            ):
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE_TWO_SEARCH_FIELDS,
                    pos=next_token.position,
                )

            # Check for opening parenthesis after term
            if (
                (
                    not re.match(self.parser.SEARCH_FIELD_REGEX, token.value)
                    and not re.match(self.parser.OPERATOR_REGEX, token.value.upper())
                    and not re.match(self.parser.PARENTHESIS_REGEX, token.value)
                    and re.match(self.parser.SEARCH_TERM_REGEX, token.value)
                )
                and (next_token.value == "(")
                and not (self.parser.tokens[index - 1].value.upper() == "NEAR")
            ):
                self.parser.add_linter_message(
                    # TODO : more detailed?
                    # message="Missing Operator between term and parenthesis.",
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE_MISSING_OPERATOR,
                    pos=token.position,
                )

            # Check for closing parenthesis after term
            if (token == ")") and (
                not re.match(self.parser.SEARCH_FIELD_REGEX, next_token.value)
                and not re.match(
                    self.parser.OPERATOR_REGEX,
                    next_token.value.upper(),
                )
                and not re.match(self.parser.PARENTHESIS_REGEX, next_token.value)
                and next_token.value not in self.language_list
                and re.match(self.parser.SEARCH_TERM_REGEX, next_token.value)
            ):
                self.parser.add_linter_message(
                    # TODO : more detailed?
                    # message="Missing Operator between term and parenthesis.",
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE_MISSING_OPERATOR,
                    pos=next_token.position,
                )

            # Check for opening parenthesis after closing parenthesis
            if (token.value == ")") and (next_token.value == "("):
                self.parser.add_linter_message(
                    # TODO: more detailed?
                    # "Missing Operator between closing and opening parenthesis.",
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE_MISSING_OPERATOR,
                    pos=token.position,
                )

            # Check for search field after term
            if (
                not re.match(self.parser.SEARCH_FIELD_REGEX, token.value)
                and not re.match(self.parser.OPERATOR_REGEX, token.value.upper())
                and not re.match(self.parser.PARENTHESIS_REGEX, token.value)
                and re.match(self.parser.SEARCH_TERM_REGEX, token.value)
            ) and re.match(self.parser.SEARCH_FIELD_REGEX, next_token.value):
                self.parser.add_linter_message(
                    # TODO : more detailed?
                    # message="Missing Operator between term and search field.",
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE_MISSING_OPERATOR,
                    pos=token.position,
                )
            index += 1

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
                QueryErrorCode.UNSUPPORTED_WILDCARD,
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

    def check_issn_isbn_format(self, token: Token) -> bool:
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
            return True
        return False

    def check_doi_format(self, token: Token) -> bool:
        """Check for the correct format of DOI."""
        token_value = token.value.replace('"', "").upper()
        if not re.match(self.parser.DOI_REGEX, token_value):
            # Add messages to self.linter_messages
            self.parser.add_linter_message(
                QueryErrorCode.DOI_FORMAT_INVALID,
                pos=token.position,
            )
            return True
        return False

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
                    QueryErrorCode.OPERATOR_CHANGED_AT_SAME_LEVEL,
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
