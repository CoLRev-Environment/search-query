#!/usr/bin/env python3
"""Web-of-Science query linter."""
import re
import typing

from search_query.constants import WOSRegex
from search_query.query import SearchField

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

    def __init__(self, parser: "search_query.parser_wos.WOSParser"):
        self.search_str = parser.query_str
        self.parser = parser

    def pre_linting(self, tokens: list, search_str: str) -> None:
        """Performs a pre-linting"""
        index = 0
        year_search_field_detected = False
        count_search_fields = 0

        if len(tokens) < 2:
            if '"' in tokens[0][0]:
                self.parser.add_linter_message(
                    rule="F0001",
                    message="The whole Search string is in quotes.",
                    position=tokens[0][1],
                )

        if tokens[0][0] in [
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
                rule="F0004",
                message="Platform identifier at the beginning detected in query.",
                position=tokens[0][1],
            )

        while index < len(tokens) - 1:
            token, span = tokens[index]
            self.check_order_of_tokens(tokens, token, span, index)

            if "NEAR" in token:
                self.check_near_distance_in_range(tokens=tokens, index=index)

            if re.match(WOSRegex.YEAR_REGEX, token):
                year_search_field_detected = True

            if re.match(WOSRegex.SEARCH_FIELD_REGEX, token):
                count_search_fields += 1

            self.check_wildcards(token=token, span=span)

            index += 1

        self.check_unsupported_wildcards(search_str=search_str)

        self.handle_multiple_same_level_operators(tokens=tokens, index=0)

        if year_search_field_detected and count_search_fields < 2:
            # Year detected without other search fields
            # TODO : should this be a fatal error? (starting with "F....")
            self.parser.add_linter_message(
                rule="E0002",
                message="Year detected without specified search field.",
                position=span,
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
                        rule="F0002",
                        message="Unmatched closing parenthesis ')'.",
                        position=(i, i + 1),
                    )

        for unmatched_index in stack:
            self.parser.add_linter_message(
                rule="F0002",
                message="Unmatched opening parenthesis '('.",
                position=(unmatched_index, unmatched_index + 1),
            )


    def check_order_of_tokens(self, tokens, token, span, index) -> None:
        """Check for the correct order of tokens in the query."""

        # Check for two operators in a row
        if re.match(WOSRegex.OPERATOR_REGEX, token) and re.match(
            WOSRegex.OPERATOR_REGEX, tokens[index + 1][0]
        ):
            self.parser.add_linter_message(
                rule="F0005",
                message="Two operators in a row.",
                position=tokens[index + 1][1],
            )

        # Check for two search fields in a row
        if re.match(WOSRegex.SEARCH_FIELD_REGEX, token) and re.match(
            WOSRegex.SEARCH_FIELD_REGEX, tokens[index + 1][0]
        ):
            self.parser.add_linter_message(
                rule="F0003",
                message="Two Search Fields in a row.",
                position=tokens[index + 1][1],
            )

        # Check for opening parenthesis after term
        if (
            (
                not re.match(WOSRegex.SEARCH_FIELD_REGEX, token)
                and not re.match(WOSRegex.OPERATOR_REGEX, token.upper())
                and not re.match(WOSRegex.PARENTHESIS_REGEX, token)
                and re.match(WOSRegex.TERM_REGEX, token)
            )
            and (tokens[index + 1][0] == "(")
            and not (tokens[index - 1][0].upper() == "NEAR")
        ):
            self.parser.add_linter_message(
                rule="F0003",
                message="Missing Operator between term and parenthesis.",
                position=span,
            )

        # Check for closing parenthesis after term
        if (token == ")") and (
            not re.match(WOSRegex.SEARCH_FIELD_REGEX, tokens[index + 1][0])
            and not re.match(WOSRegex.OPERATOR_REGEX, tokens[index + 1][0].upper())
            and not re.match(WOSRegex.PARENTHESIS_REGEX, tokens[index + 1][0])
            and tokens[index + 1][0] not in self.language_list
            and re.match(WOSRegex.TERM_REGEX, tokens[index + 1][0])
        ):
            self.parser.add_linter_message(
                rule="F0003",
                message="Missing Operator between term and parenthesis.",
                position=tokens[index + 1][1],
            )

        # Check for opening parenthesis after closing parenthesis
        if (token == ")") and (tokens[index + 1][0] == "("):
            self.parser.add_linter_message(
                rule="F0003",
                message="Missing Operator between closing and opening parenthesis.",
                position=span,
            )

        # Check for search field after term
        if (
            not re.match(WOSRegex.SEARCH_FIELD_REGEX, token)
            and not re.match(WOSRegex.OPERATOR_REGEX, token.upper())
            and not re.match(WOSRegex.PARENTHESIS_REGEX, token)
            and re.match(WOSRegex.TERM_REGEX, token)
        ) and re.match(WOSRegex.SEARCH_FIELD_REGEX, tokens[index + 1][0]):
            self.parser.add_linter_message(
                rule="F0003",
                message="Missing Operator between term and search field.",
                position=span,
            )

    def check_near_distance_in_range(self, tokens: list, index: int) -> None:
        """Check for NEAR with a specified distance out of range."""
        near_distance = re.findall(r"\d{1,2}", tokens[index][0])
        if near_distance and int(near_distance[0]) > 15:
            self.parser.add_linter_message(
                rule="F0006",
                message="NEAR operator distance out of range (max. 15).",
                position=tokens[index][1],
            )

    def check_unsupported_wildcards(self, search_str: str) -> None:
        """Check for unsupported characters in the search string."""

        matches = re.findall(WOSRegex.UNSUPPORTED_WILDCARD_REGEX, search_str)
        if matches:
            for unsupported_wildcard in matches:
                self.parser.add_linter_message(
                    rule="F1001",
                    message=(
                        "Unsupported wildcard in search string: " + unsupported_wildcard
                    ),
                    position=(
                        search_str.find(unsupported_wildcard),
                        search_str.find(unsupported_wildcard) + 1,
                    ),
                )

        # Check if a wildcard is used as standalone
        for index, charachter in enumerate(search_str):
            if charachter in ["?", "$", "*"]:
                # Check if wildcard is left or right-handed or standalone
                if (search_str[index - 1] == "" or search_str[index - 1] == '"') and (
                    search_str[index + 1] == "" or search_str[index + 1] == '"'
                ):
                    # Standalone wildcard usage
                    self.parser.add_linter_message(
                        rule="F1002",
                        message="Wildcard "
                        + charachter
                        + " should not be used as standalone.",
                        position=(index, index + 1),
                    )
                    break

    def check_wildcards(self, token: str, span: tuple) -> None:
        """Check for the usage of wildcards in the search string."""

        token = token.replace('"', "")

        # Implement constrains from Web of Science for Wildcards
        for index, charachter in enumerate(token):
            if charachter in ["?", "$", "*"]:
                # Check if wildcard is left or right-handed or standalone
                if index == 0 and len(token) == 1:
                    # TODO : self.parser.add_linter_message(...)
                    print("TODO")

                elif len(token) == index + 1:
                    # Right-hand wildcard
                    self.check_unsupported_right_hand_wildcards(
                        token=token, index=index, span=span
                    )

                elif index == 0 and len(token) > 1:
                    # Left-hand wildcard
                    self.check_format_left_hand_wildcards(token=token, span=span)

                else:
                    # Wildcard in the middle of the term
                    if token[index - 1] in ["/", "@", "#", ".", ":", ";", "!"]:
                        self.parser.add_linter_message(
                            rule="F1001",
                            message="Do not use wildcard after a special character.",
                            position=span,
                        )

    def check_unsupported_right_hand_wildcards(
        self, token: str, index: int, span: tuple
    ) -> None:
        """Check for unsupported right-hand wildcards in the search string."""

        if token[index - 1] in ["/", "@", "#", ".", ":", ";", "!"]:
            self.parser.add_linter_message(
                rule="F1001",
                message="Do not use wildcard after a special character.",
                position=span,
            )

        if len(token) < 4:
            self.parser.add_linter_message(
                rule="F1001",
                message="Right-hand wildcard must preceded by at least three characters.",
                position=span,
            )

    def check_format_left_hand_wildcards(self, token: str, span: tuple) -> None:
        """Check for wrong usage among left-hand wildcards in the search string."""

        if len(token) < 4:
            self.parser.add_linter_message(
                rule="F1001",
                message="Left-hand wildcard must be followed by at least three characters.",
                position=span,
            )

    def check_issn_isbn_format(self, token: str, search_field: SearchField) -> bool:
        """Check for the correct format of ISSN and ISBN."""
        token = token.replace('"', "")
        if not re.match(WOSRegex.ISSN_REGEX, token) and not re.match(
            WOSRegex.ISBN_REGEX, token
        ):
            # Add messages to self.linter_messages
            self.parser.add_linter_message(
                rule="F0008",
                message="ISSN/ISBN format is incorrect.",
                position=search_field.position,
            )
            return True
        return False

    def check_doi_format(self, token: str, search_field: SearchField) -> bool:
        """Check for the correct format of DOI."""
        token = token.replace('"', "").upper()
        if not re.match(WOSRegex.DOI_REGEX, token):
            # Add messages to self.linter_messages
            self.parser.add_linter_message(
                rule="F0008",
                message="DOI format is incorrect.",
                position=search_field.position,
            )
            return True
        return False

    def handle_multiple_same_level_operators(self, tokens: list, index: int) -> int:
        """Handle multiple same level operators."""
        # This function introduces additional parantheses to the query tree
        # based on the precedence of the operators.
        # Precedence: NEAR > SAME > NOT > AND > OR
        operator_list = []
        clear_list = False
        while index < len(tokens):
            token, span = tokens[index]

            if token == "(":
                index = self.handle_multiple_same_level_operators(
                    tokens=tokens, index=index + 1
                )

            if token == ")":
                return index

            # Operator change
            if (
                operator_list
                and re.match(WOSRegex.OPERATOR_REGEX, token.upper())
                and token.upper() not in operator_list
                and token.upper() != "NOT"
            ):
                self.parser.add_linter_message(
                    rule="F0007",
                    message="The operator changed at the same level."
                    + " Please introduce parentheses.",
                    position=span,
                )

                clear_list = True

            # Clear the operator list after inserting parentheses
            if clear_list:
                operator_list.clear()
                clear_list = False

            if token.upper() in ["NEAR", "AND", "OR", "NOT"] or "NEAR" in token.upper():
                operator_list.append(token.upper())
            index += 1
        return index
