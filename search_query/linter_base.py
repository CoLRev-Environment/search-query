#!/usr/bin/env python3
"""Validator for search queries."""
from __future__ import annotations

import re
import typing

import search_query.parser_base
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes


# Could indeed be a general Validator class
class QueryStringLinter:
    """Class for Query String Validation"""

    FAULTY_OPERATOR_REGEX = r"\b(?:[aA][nN][dD]|[oO][rR]|[nN][oO][tT])\b"
    PARENTHESIS_REGEX = r"[\(\)]"

    def __init__(
        self,
        parser: search_query.parser_base.QueryStringParser,
    ):
        self.query_str = parser.query_str
        self.search_field_general = parser.search_field_general
        self.parser = parser
        self.messages: typing.List[dict] = []

    def add_linter_message(
        self, error: QueryErrorCode, *, position: tuple, details: str = ""
    ) -> None:
        """Add a linter message."""
        # do not add duplicates
        if any(
            error.code == msg["code"] and position == msg["position"]
            for msg in self.messages
        ):
            return

        self.messages.append(
            {
                "code": error.code,
                "label": error.label,
                "message": error.message,
                "is_fatal": error.is_fatal(),
                "position": position,
                "details": details,
            }
        )

    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors."""
        return any(m["is_fatal"] for m in self.messages)

    def check_missing_tokens(self) -> None:
        """Check missing tokens"""
        covered_ranges = []
        current_index = 0

        for token in self.parser.tokens:
            token_value = token.value
            try:
                start = self.parser.query_str.index(token_value, current_index)
                end = start + len(token_value)
                covered_ranges.append((start, end))
                current_index = end
            except ValueError:
                continue  # Token not found

        # Merge overlapping/adjacent ranges
        merged: list = []
        for start, end in sorted(covered_ranges):
            if not merged or merged[-1][1] < start:
                merged.append((start, end))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))

        # Identify gaps and add linter messages
        last_end = 0
        for start, end in merged:
            if last_end < start:
                segment = self.parser.query_str[last_end:start]
                if segment.strip():  # non-whitespace segment
                    self.add_linter_message(
                        QueryErrorCode.TOKENIZING_FAILED,
                        position=(last_end, start),
                        details=f"Unparsed segment: '{segment.strip()}'",
                    )
            last_end = end

        # Handle trailing unparsed text
        if last_end < len(self.parser.query_str):
            segment = self.parser.query_str[last_end:]
            if segment.strip():
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED,
                    position=(last_end, len(self.parser.query_str)),
                    details=f"Unparsed segment: '{segment.strip()}'",
                )

    def check_quoted_search_terms(self) -> None:
        """Check quoted search terms."""
        for token in self.parser.tokens:
            if token.type != TokenTypes.SEARCH_TERM:
                continue
            if '"' not in token.value:
                continue

            if token.value[0] != '"' or token.value[-1] != '"':
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED,
                    position=token.position,
                    details=f"Token '{token.value}' should be fully quoted",
                )

    def check_operator_capitalization(self) -> None:
        """Check if operators are capitalized."""
        for token in self.parser.tokens:
            if token.type == TokenTypes.LOGIC_OPERATOR:
                if token.value != token.value.upper():
                    self.add_linter_message(
                        QueryErrorCode.OPERATOR_CAPITALIZATION,
                        position=token.position,
                    )
                    token.value = token.value.upper()

    def check_unbalanced_parentheses(self) -> None:
        """Check query for unbalanced parentheses."""
        i = 0
        for token in self.parser.tokens:
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                i += 1
            if token.type == TokenTypes.PARENTHESIS_CLOSED:
                if i == 0:
                    self.add_linter_message(
                        QueryErrorCode.UNBALANCED_PARENTHESES,
                        position=token.position,
                        details="Unbalanced closing parenthesis",
                    )
                else:
                    i -= 1
        if i > 0:
            # Query contains unbalanced opening parentheses
            i = 0
            for token in reversed(self.parser.tokens):
                if token.type == TokenTypes.PARENTHESIS_CLOSED:
                    i += 1
                if token.type == TokenTypes.PARENTHESIS_OPEN:
                    if i == 0:
                        self.add_linter_message(
                            QueryErrorCode.UNBALANCED_PARENTHESES,
                            position=token.position,
                            details="Unbalanced opening parenthesis",
                        )
                    else:
                        i -= 1

    def check_unknown_token_types(self) -> None:
        """Check for unknown token types."""
        for token in self.parser.tokens:
            if token.type == TokenTypes.UNKNOWN:
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED, position=token.position
                )

    def check_invalid_characters_in_search_term(self, invalid_characters: str) -> None:
        """Check a search term for invalid characters"""

        for token in self.parser.tokens:
            if token.type != TokenTypes.SEARCH_TERM:
                continue
            value = token.value

            # Iterate over term to identify invalid characters
            # and replace them with whitespace
            for char in token.value:
                if char in invalid_characters:
                    self.add_linter_message(
                        QueryErrorCode.INVALID_CHARACTER, position=token.position
                    )
                    # TBD: really change?
                    # value = value[:i] + " " + value[i + 1 :]
            # Update token
            if value != token.value:
                token.value = value

    def check_near_distance_in_range(self, *, max_value: int) -> None:
        """Check for NEAR with a specified distance out of range."""
        for token in self.parser.tokens:
            if token.type != TokenTypes.PROXIMITY_OPERATOR:
                continue
            near_distance = re.findall(r"\d{1,2}", token.value)
            if near_distance and int(near_distance[0]) > max_value:
                self.add_linter_message(
                    QueryErrorCode.NEAR_DISTANCE_TOO_LARGE,
                    position=token.position,
                )

    def check_boolean_operator_readability(
        self, *, faulty_operators: str = "|&"
    ) -> None:
        """Check for readability of boolean operators."""
        for token in self.parser.tokens:
            if token.type == TokenTypes.LOGIC_OPERATOR:
                if token.value in faulty_operators:
                    self.add_linter_message(
                        QueryErrorCode.BOOLEAN_OPERATOR_READABILITY,
                        position=token.position,
                        details="Please use AND, OR, NOT instead of |&",
                    )
                    # Replace?

    def handle_fully_quoted_query_str(self) -> None:
        """Handle fully quoted query string."""
        if (
            '"' == self.parser.query_str[0]
            and '"' == self.parser.query_str[-1]
            and "(" in self.parser.query_str
        ):
            self.add_linter_message(
                QueryErrorCode.QUERY_IN_QUOTES,
                position=(-1, -1),
            )
            # remove quotes before tokenization
            self.parser.query_str = self.parser.query_str[1:-1]

    def add_higher_value(
        self,
        output: list[Token],
        current_value: int,
        value: int,
        art_par: int,
    ) -> tuple[list[Token], int]:
        """Adds open parenthesis to higher value operators"""
        temp: list[Token] = []
        depth_lvl = 0  # Counter for actual parenthesis

        while output:
            # Get previous tokens until right operator has been reached
            token = output.pop()

            # Track already existing and correct query blocks
            if token.type == TokenTypes.PARENTHESIS_CLOSED:
                depth_lvl += 1
            elif token.type == TokenTypes.PARENTHESIS_OPEN:
                depth_lvl -= 1

            temp.insert(0, token)

            if (
                token.type in [TokenTypes.LOGIC_OPERATOR, TokenTypes.PROXIMITY_OPERATOR]
                and depth_lvl == 0
            ):
                # Insert open parenthesis
                # depth_lvl ensures that already existing blocks are ignored

                # Insert open parenthesis after operator
                while current_value < value:
                    self.add_linter_message(
                        QueryErrorCode.IMPLICIT_PRECEDENCE,
                        position=token.position,
                    )
                    # Insert open parenthesis after operator
                    temp.insert(
                        1,
                        Token(
                            value="(",
                            type=TokenTypes.PARENTHESIS_OPEN,
                            position=(-1, -1),
                        ),
                    )
                    current_value += 1
                    art_par += 1
                break

        return temp, art_par

    def flatten_redundant_artificial_nesting(self, tokens: list[Token]) -> None:
        """
        Flattens redundant artificial nesting:
        If two artificial open parens are followed eventually by
        two artificial close parens at the same level, removes the outer ones.
        """

        while True:
            len_initial = len(tokens)

            output = []
            i = 0
            while i < len(tokens):
                # Look ahead for double artificial opening
                if (
                    i + 1 < len(tokens)
                    and tokens[i].type == TokenTypes.PARENTHESIS_OPEN
                    and tokens[i + 1].type == TokenTypes.PARENTHESIS_OPEN
                    and tokens[i].position == (-1, -1)
                    and tokens[i + 1].position == (-1, -1)
                ):
                    # Look for matching double closing
                    inner_start = i + 2
                    depth = 2
                    j = inner_start
                    while j < len(tokens) and depth > 0:
                        if tokens[j].type == TokenTypes.PARENTHESIS_OPEN and tokens[
                            j
                        ].position == (-1, -1):
                            depth += 1
                        elif tokens[j].type == TokenTypes.PARENTHESIS_CLOSED and tokens[
                            j
                        ].position == (-1, -1):
                            depth -= 1
                        j += 1

                    # Check for double artificial closing
                    if (
                        j < len(tokens)
                        and tokens[j - 1].type == TokenTypes.PARENTHESIS_CLOSED
                        and tokens[j - 2].type == TokenTypes.PARENTHESIS_CLOSED
                        and tokens[j - 1].position == (-1, -1)
                        and tokens[j - 2].position == (-1, -1)
                    ):
                        # Skip outer pair
                        output.extend(tokens[i + 1 : j - 1])
                        i = j

                        continue

                output.append(tokens[i])
                i += 1

            # Repeat for multiple nestings
            if len_initial == len(output):
                break
            tokens = output

        self.parser.tokens = output

    # pylint: disable=too-many-branches
    def add_artificial_parentheses_for_operator_precedence(
        self,
        index: int = 0,
        output: typing.Optional[list] = None,
    ) -> tuple[int, list[Token]]:
        """
        Adds artificial parentheses with position (-1, -1)
        to enforce operator precedence.
        """
        if output is None:
            output = []
        # Value of operator
        value = 0
        # Value of previous operator
        current_value = -1
        # Added artificial parentheses
        art_par = 0

        while index < len(self.parser.tokens):
            # Forward iteration through tokens

            if self.parser.tokens[index].type == TokenTypes.PARENTHESIS_OPEN:
                output.append(self.parser.tokens[index])
                index += 1
                index, output = self.add_artificial_parentheses_for_operator_precedence(
                    index, output
                )
                continue

            if self.parser.tokens[index].type == TokenTypes.PARENTHESIS_CLOSED:
                output.append(self.parser.tokens[index])
                index += 1
                # Add closed parenthesis in case there are still open ones
                while art_par > 0:
                    output.append(
                        Token(
                            value=")",
                            type=TokenTypes.PARENTHESIS_CLOSED,
                            position=(-1, -1),
                        )
                    )
                    art_par -= 1
                return index, output

            if self.parser.tokens[index].type in [
                TokenTypes.LOGIC_OPERATOR,
                TokenTypes.PROXIMITY_OPERATOR,
            ]:
                value = self.parser.get_precedence(self.parser.tokens[index].value)

                if current_value in (value, -1):
                    # Same precedence → just add to output
                    output.append(self.parser.tokens[index])
                    current_value = value

                elif value > current_value:
                    # Higher precedence → start wrapping with artificial parenthesis
                    temp, art_par = self.add_higher_value(
                        output, current_value, value, art_par
                    )

                    output.extend(temp)
                    output.append(self.parser.tokens[index])
                    current_value = value

                elif value < current_value:
                    # Insert close parenthesis for each point in value difference
                    while current_value > value:
                        self.add_linter_message(
                            QueryErrorCode.IMPLICIT_PRECEDENCE,
                            position=self.parser.tokens[index].position,
                        )
                        # Lower precedence → close parenthesis
                        output.append(
                            Token(
                                value=")",
                                type=TokenTypes.PARENTHESIS_CLOSED,
                                position=(-1, -1),
                            )
                        )
                        current_value -= 1
                        art_par -= 1
                    output.append(self.parser.tokens[index])
                    current_value = value

                index += 1
                continue

            # Default: search terms, fields, etc.
            output.append(self.parser.tokens[index])
            index += 1

        # Add parenthesis in case there are missing ones
        if art_par > 0:
            while art_par > 0:
                output.append(
                    Token(
                        value=")", type=TokenTypes.PARENTHESIS_CLOSED, position=(-1, -1)
                    )
                )
                art_par -= 1
        if art_par < 0:
            while art_par < 0:
                output.insert(
                    0,
                    Token(
                        value="(", type=TokenTypes.PARENTHESIS_OPEN, position=(-1, -1)
                    ),
                )
                art_par += 1

        if index == len(self.parser.tokens):
            self.flatten_redundant_artificial_nesting(output)

        return index, output


class QueryListLinter:
    """Class for Query List Validation"""

    def __init__(
        self,
        parser: search_query.parser_base.QueryListParser,
        string_parser_class: typing.Type[search_query.parser_base.QueryStringParser],
    ):
        self.parser = parser
        self.messages: dict = {}
        self.string_parser_class = string_parser_class

    def add_linter_message(
        self,
        error: QueryErrorCode,
        *,
        list_position: int,
        position: tuple,
        details: str = "",
    ) -> None:
        """Add a linter message."""
        # do not add duplicates
        if any(
            error.code == msg["code"] and position == msg["position"]
            for msg in self.messages.get(list_position, [])
        ):
            return
        if list_position not in self.messages:
            self.messages[list_position] = []

        self.messages[list_position].append(
            {
                "code": error.code,
                "label": error.label,
                "message": error.message,
                "is_fatal": error.is_fatal(),
                "position": position,
                "details": details,
            }
        )

    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors."""
        return any(d["is_fatal"] for e in self.messages.values() for d in e)
