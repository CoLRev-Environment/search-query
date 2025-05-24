#!/usr/bin/env python3
"""Validator for search queries."""
from __future__ import annotations

import re
import sys
import typing
from abc import abstractmethod
from collections import defaultdict

import search_query.parser_base
from search_query.constants import Colors
from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import ListQuerySyntaxError
from search_query.exception import QuerySyntaxError
from search_query.utils import format_query_string_positions

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


# pylint: disable=too-many-public-methods
# pylint: disable=too-many-lines


# Could indeed be a general Validator class
class QueryStringLinter:
    """Class for Query String Validation"""

    FAULTY_OPERATOR_REGEX = r"\b(?:[aA][nN][dD]|[oO][rR]|[nN][oO][tT])\b"
    PARENTHESIS_REGEX = r"[\(\)]"

    # Higher number=higher precedence
    OPERATOR_PRECEDENCE = {
        "NEAR": 3,
        "WITHIN": 3,
        "NOT": 2,
        "AND": 1,
        "OR": 0,
    }
    PLATFORM: PLATFORM = PLATFORM.GENERIC
    VALID_FIELDS_REGEX: re.Pattern

    def __init__(self, query_str: str) -> None:
        self.tokens: typing.List[Token] = []

        self.query_str = query_str
        # Note: original, unchanged query string
        self._original_query_str = query_str
        self.search_field_general = ""
        self.query: typing.Optional[Query] = None
        self.messages: typing.List[dict] = []
        self.last_read_index = 0

    def add_linter_message(
        self,
        error: QueryErrorCode,
        *,
        positions: typing.Sequence[tuple],
        details: str = "",
    ) -> None:
        """Add a linter message."""
        # do not add duplicates
        if any(
            error.code == msg["code"] and positions == msg["position"]
            for msg in self.messages
        ):
            return

        self.messages.append(
            {
                "code": error.code,
                "label": error.label,
                "message": error.message,
                "is_fatal": error.is_fatal(),
                "position": positions,
                "details": details,
            }
        )

    def print_messages(self) -> None:
        """Print the latest linter messages."""
        if not self.messages:
            return

        grouped_messages = defaultdict(list)
        utf_output = str(sys.stdout.encoding).lower().startswith("utf")

        for message in self.messages[self.last_read_index :]:
            grouped_messages[message["code"]].append(message)

        for code, group in grouped_messages.items():
            # Take the first message as representative
            representative = group[0]
            color = Colors.ORANGE
            category = "Info"

            if code.startswith("F"):
                color = Colors.RED
                category = "❌" if utf_output else "X"
                category += " Fatal"
            elif code.startswith("E"):
                category = "⚠️" if utf_output else "-"
                category += " Error"
            elif code.startswith("W"):
                category = "💡" if utf_output else "i"
                category += " Warning"

            print(
                f"{color}{category}{Colors.END}: " f"{representative['label']} ({code})"
            )
            consolidated_messages = []
            for message in group:
                if message["details"]:
                    consolidated_messages.append(f"  {message['details']}")
                else:
                    consolidated_messages.append(f"  {message['message']}")
            for item in set(consolidated_messages):
                print(item)
            positions = [pos for message in group for pos in message["position"]]
            query_info = format_query_string_positions(
                self._original_query_str,
                positions,
                color=color,
            )
            print(f"  {query_info}")

        self.last_read_index = len(self.messages)

    def check_status(self) -> None:
        """Check the output of the linter and report errors to the user"""

        # Collecting messages instead of printing them immediately
        # allows us to consolidate messages with the same code or even replace messages
        # This means that we need to raise the exception only once (at the end)

        self.print_messages()

        if self.has_fatal_errors():
            # OR any (code.is_error() for code in messages)
            # and self.parser.mode == "strict":
            raise QuerySyntaxError(self)

    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors."""
        return any(m["is_fatal"] for m in self.messages)

    @abstractmethod
    def validate_tokens(
        self,
        *,
        tokens: typing.List[Token],
        query_str: str,
        search_field_general: str = "",
    ) -> typing.List[Token]:
        """Validate tokens"""

    @abstractmethod
    def validate_query_tree(self, query: Query) -> None:
        """Validate query tree"""

    def check_missing_tokens(self) -> None:
        """Check missing tokens"""
        covered_ranges = []
        current_index = 0

        for token in self.tokens:
            token_value = token.value
            try:
                start = self.query_str.index(token_value, current_index)
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
                segment = self.query_str[last_end:start]
                if segment.strip():  # non-whitespace segment
                    self.add_linter_message(
                        QueryErrorCode.TOKENIZING_FAILED,
                        positions=[(last_end, start)],
                        details=f"Unparsed segment: '{segment.strip()}'",
                    )
            last_end = end

        # Handle trailing unparsed text
        if last_end < len(self.query_str):
            segment = self.query_str[last_end:]
            if segment.strip():
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED,
                    positions=[(last_end, len(self.query_str))],
                    details=f"Unparsed segment: '{segment.strip()}'",
                )

    def check_unsupported_search_fields_in_query(self, query: Query) -> None:
        """Check for the correct format of fields.

        Note: compile valid_field_regex with/out flags=re.IGNORECASE
        """

        if query.search_field:
            # pylint: disable=no-member
            if not self.VALID_FIELDS_REGEX.match(query.search_field.value):  # type: ignore
                pos_info = ""
                if query.search_field.position:
                    pos_info = f" at position {query.search_field.position}"
                details = (
                    f"Search field {query.search_field}{pos_info} is not supported."
                )
                details += f" Supported fields for {self.PLATFORM}: "
                details += f"{self.VALID_FIELDS_REGEX.pattern}"
                self.add_linter_message(
                    QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                    positions=[query.search_field.position or (-1, -1)],
                    details=details,
                )

        for child in query.children:
            self.check_unsupported_search_fields_in_query(child)

    def check_operator_capitalization(self) -> None:
        """Check if operators are capitalized."""
        for token in self.tokens:
            if token.type == TokenTypes.LOGIC_OPERATOR:
                if token.value != token.value.upper():
                    self.add_linter_message(
                        QueryErrorCode.OPERATOR_CAPITALIZATION,
                        positions=[token.position],
                    )
                    token.value = token.value.upper()

    def check_unbalanced_parentheses(self) -> None:
        """Check query for unbalanced parentheses."""
        i = 0
        for token in self.tokens:
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                i += 1
            if token.type == TokenTypes.PARENTHESIS_CLOSED:
                if i == 0:
                    self.add_linter_message(
                        QueryErrorCode.UNBALANCED_PARENTHESES,
                        positions=[token.position],
                        details="Unbalanced closing parenthesis",
                    )
                else:
                    i -= 1
        if i > 0:
            # Query contains unbalanced opening parentheses
            i = 0
            for token in reversed(self.tokens):
                if token.type == TokenTypes.PARENTHESIS_CLOSED:
                    i += 1
                if token.type == TokenTypes.PARENTHESIS_OPEN:
                    if i == 0:
                        self.add_linter_message(
                            QueryErrorCode.UNBALANCED_PARENTHESES,
                            positions=[token.position],
                            details="Unbalanced opening parenthesis",
                        )
                    else:
                        i -= 1

    def check_unbalanced_quotes_in_terms(self, query: Query) -> None:
        """Recursively check for unbalanced quotes in quoted search terms."""

        if query.is_term():
            value = query.value.strip()
            if '"' not in value:
                return

            quote_count = value.count('"')

            # Case 1: Properly quoted (e.g., "AI")
            if quote_count == 2 and value.startswith('"') and value.endswith('"'):
                return

            # Case 2: unmatched opening quote
            if value.startswith('"') and not value.endswith('"'):
                self.add_linter_message(
                    QueryErrorCode.UNBALANCED_QUOTES,
                    positions=[query.position or (-1, -1)],
                    details="Unmatched opening quote",
                )

            # Case 3: unmatched closing quote
            elif value.endswith('"') and not value.startswith('"'):
                self.add_linter_message(
                    QueryErrorCode.UNBALANCED_QUOTES,
                    positions=[query.position or (-1, -1)],
                    details="Unmatched closing quote",
                )

            # Case 4: unbalanced or excessive quotes
            elif quote_count % 2 != 0:
                self.add_linter_message(
                    QueryErrorCode.UNBALANCED_QUOTES,
                    positions=[query.position or (-1, -1)],
                    details="Unbalanced quotes inside term",
                )
            elif quote_count % 2 == 0:
                self.add_linter_message(
                    QueryErrorCode.UNBALANCED_QUOTES,
                    positions=[query.position or (-1, -1)],
                    details="Suspicious or excessive quote usage",
                )

            return

        for child in query.children:
            self.check_unbalanced_quotes_in_terms(child)

    def check_unknown_token_types(self) -> None:
        """Check for unknown token types."""
        for token in self.tokens:
            if token.type == TokenTypes.UNKNOWN:
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED, positions=[token.position]
                )

    def check_invalid_characters_in_search_term(self, invalid_characters: str) -> None:
        """Check a search term for invalid characters"""

        for token in self.tokens:
            if token.type != TokenTypes.SEARCH_TERM:
                continue
            value = token.value

            # Iterate over term to identify invalid characters
            # and replace them with whitespace
            for char in token.value:
                if char in invalid_characters:
                    self.add_linter_message(
                        QueryErrorCode.INVALID_CHARACTER, positions=[token.position]
                    )
                    # TBD: really change?
                    # value = value[:i] + " " + value[i + 1 :]
            # Update token
            if value != token.value:
                token.value = value

    def check_near_distance_in_range(self, *, max_value: int) -> None:
        """Check for NEAR with a specified distance out of range."""
        for token in self.tokens:
            if token.type != TokenTypes.PROXIMITY_OPERATOR:
                continue
            near_distance = re.findall(r"\d{1,2}", token.value)
            if near_distance and int(near_distance[0]) > max_value:
                self.add_linter_message(
                    QueryErrorCode.NEAR_DISTANCE_TOO_LARGE,
                    positions=[token.position],
                )

    def check_boolean_operator_readability_query(
        self, query: Query, *, faulty_operators: str = "|&"
    ) -> None:
        """Check for readability of boolean operators."""

        if query.operator:
            if query.value in faulty_operators:
                self.add_linter_message(
                    QueryErrorCode.BOOLEAN_OPERATOR_READABILITY,
                    positions=[query.position or (-1, -1)],
                    details="Please use AND, OR, NOT instead of |&",
                )
                # Replace?

        for child in query.children:
            self.check_boolean_operator_readability_query(
                child, faulty_operators=faulty_operators
            )

    def handle_fully_quoted_query_str(self, query_str: str) -> str:
        """Handle fully quoted query string."""
        if '"' == query_str[0] and '"' == query_str[-1] and "(" in query_str:
            self.add_linter_message(
                QueryErrorCode.QUERY_IN_QUOTES,
                positions=[(-1, -1)],
            )
            # remove quotes before tokenization
            query_str = query_str[1:-1]
        return query_str

    def handle_nonstandard_quotes_in_query_str(self, query_str: str) -> str:
        """Handle non-standard quotes in query string."""

        non_standard_quotes = "“”«»„‟"
        positions = []
        found_quotes = []
        for quote in non_standard_quotes:
            quote_positions = [
                (i, i + 1) for i, c in enumerate(query_str) if c == quote
            ]
            if not quote_positions:
                continue
            positions.extend(quote_positions)
            found_quotes.append(quote)
            # Replace all occurrences of this quote with standard quote
            query_str = query_str.replace(quote, '"')
        if positions:
            self.add_linter_message(
                QueryErrorCode.NON_STANDARD_QUOTES,
                positions=positions,
                details=f"Non-standard quotes found: {''.join(sorted(found_quotes))}",
            )

        return query_str

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
                        positions=[token.position],
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

        self.tokens = output

    def get_precedence(self, token: str) -> int:
        """Returns operator precedence for logical and proximity operators."""

        if token in self.OPERATOR_PRECEDENCE:
            return self.OPERATOR_PRECEDENCE[token]
        return -1  # Not an operator

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

        while index < len(self.tokens):
            # Forward iteration through tokens

            if self.tokens[index].type == TokenTypes.PARENTHESIS_OPEN:
                output.append(self.tokens[index])
                index += 1
                index, output = self.add_artificial_parentheses_for_operator_precedence(
                    index, output
                )
                continue

            if self.tokens[index].type == TokenTypes.PARENTHESIS_CLOSED:
                output.append(self.tokens[index])
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

            if self.tokens[index].type in [
                TokenTypes.LOGIC_OPERATOR,
                TokenTypes.PROXIMITY_OPERATOR,
            ]:
                value = self.get_precedence(self.tokens[index].value)

                if current_value in (value, -1):
                    # Same precedence → just add to output
                    output.append(self.tokens[index])
                    current_value = value

                elif value > current_value:
                    # Higher precedence → start wrapping with artificial parenthesis
                    temp, art_par = self.add_higher_value(
                        output, current_value, value, art_par
                    )

                    output.extend(temp)
                    output.append(self.tokens[index])
                    current_value = value

                elif value < current_value:
                    # Insert close parenthesis for each point in value difference
                    while current_value > value:
                        self.add_linter_message(
                            QueryErrorCode.IMPLICIT_PRECEDENCE,
                            positions=[self.tokens[index].position],
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
                    output.append(self.tokens[index])
                    current_value = value

                index += 1
                continue

            # Default: search terms, fields, etc.
            output.append(self.tokens[index])
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

        if index == len(self.tokens):
            self.flatten_redundant_artificial_nesting(output)

        return index, output

    def get_query_with_fields_at_terms(self, query: Query) -> Query:
        """Move the search field from the operator to the terms.

        Note: utility function for validating search terms
        with efficient access to search fields (at the level of terms).

        """
        modified_query = query.copy()
        if modified_query.operator and modified_query.search_field:
            # move search field from operator to terms
            for child in modified_query.children:
                if not child.search_field:
                    child.search_field = modified_query.search_field.copy()
            modified_query.search_field = None

        for i, child in enumerate(modified_query.children):
            modified_query.children[i] = self.get_query_with_fields_at_terms(child)

        return modified_query

    def check_operator_capitalization_query(self, query: Query) -> None:
        """Check if operators are capitalized."""

        if query.operator:
            if query.value != query.value.upper():
                self.add_linter_message(
                    QueryErrorCode.OPERATOR_CAPITALIZATION,
                    positions=[query.position or (-1, -1)],
                )
                query.value = query.value.upper()

        for child in query.children:
            self.check_operator_capitalization_query(child)

    def check_invalid_characters_in_search_term_query(
        self, query: Query, invalid_characters: str
    ) -> None:
        """Check a search term for invalid characters"""

        if query.is_term():
            # Iterate over term to identify invalid characters
            # and replace them with whitespace
            for char in invalid_characters:
                if char in query.value:
                    self.add_linter_message(
                        QueryErrorCode.INVALID_CHARACTER,
                        positions=[query.position or (-1, -1)],
                    )
                    # TBD: really change?
                    # value = value[:i] + " " + value[i + 1 :]
            # Update token
            if query.value != query.value:
                query.value = query.value

        for child in query.children:
            self.check_invalid_characters_in_search_term_query(
                child, invalid_characters
            )

    def check_operators_with_fields(self, query: Query) -> None:
        """Check for operators with fields"""

        if query.operator and query.search_field:
            self.add_linter_message(
                QueryErrorCode.NESTED_QUERY_WITH_SEARCH_FIELD,
                positions=[query.position or (-1, -1)],
                details="Nested query (operator) with search field is not supported",
            )

        for child in query.children:
            self.check_operators_with_fields(child)

    @abstractmethod
    def syntax_str_to_generic_search_field_set(self, field_value: str) -> set[Fields]:
        """Translate a search field"""

    def _check_date_filters_in_subquery(self, query: Query, level: int = 0) -> None:
        """Check for date filters in subqueries"""

        # Skip top-level queries
        if level == 0:
            for child in query.children:
                try:
                    self._check_date_filters_in_subquery(child, level + 1)
                except ValueError:
                    pass
            return
        if query.operator:
            for child in query.children:
                try:
                    self._check_date_filters_in_subquery(child, level + 1)
                except ValueError:
                    pass
            return

        if not query.search_field:
            return

        generic_fields = self.syntax_str_to_generic_search_field_set(
            query.search_field.value
        )
        if generic_fields & {Fields.PUBLICATION_DATE}:
            details = (
                "Please double-check whether date filters "
                "should apply to the entire query."
            )
            self.add_linter_message(
                QueryErrorCode.DATE_FILTER_IN_SUBQUERY,
                positions=[query.position or (-1, -1)],
                details=details,
            )

    def _check_journal_filters_in_subquery(self, query: Query, level: int = 0) -> None:
        """Check for journal filters in subqueries"""

        # Skip top-level queries
        if level == 0:
            for child in query.children:
                try:
                    self._check_journal_filters_in_subquery(child, level + 1)
                except ValueError:
                    pass
            return
        if query.operator:
            for child in query.children:
                try:
                    self._check_journal_filters_in_subquery(child, level + 1)
                except ValueError:
                    pass
            return

        if not query.search_field:
            return

        generic_fields = self.syntax_str_to_generic_search_field_set(
            query.search_field.value
        )
        if generic_fields & {Fields.JOURNAL, Fields.PUBLICATION_NAME}:
            details = (
                "Please double-check whether journal/publication-name filters "
                f"({query.search_field.value}) should apply to the entire query."
            )
            self.add_linter_message(
                QueryErrorCode.JOURNAL_FILTER_IN_SUBQUERY,
                positions=[query.position or (-1, -1)],
                details=details,
            )

    def _extract_subqueries(
        self, query: Query, subqueries: dict, subquery_types: dict, subquery_id: int = 0
    ) -> None:
        """Extract subqueries from query tree"""
        if subquery_id not in subqueries:
            subqueries[subquery_id] = []
            if query.operator:
                subquery_types[subquery_id] = query.value

        for child in query.children:
            if not child.children:
                subqueries[subquery_id].append(child)
            elif child.value == query.value:
                self._extract_subqueries(child, subqueries, subquery_types, subquery_id)
            else:
                new_subquery_id = max(subqueries.keys()) + 1
                self._extract_subqueries(
                    child, subqueries, subquery_types, new_subquery_id
                )

        if not query.children:
            subqueries[subquery_id].append(query)

    # pylint: disable=too-many-branches
    def _check_redundant_terms(self, query: Query) -> None:
        """Check query for redundant search terms"""
        subqueries: dict = {}
        subquery_types: dict = {}
        self._extract_subqueries(query, subqueries, subquery_types)

        # Compare search terms in the same subquery for redundancy
        for query_id, terms in subqueries.items():
            # Exclude subqueries without search terms
            if not terms:
                continue

            if query_id not in subquery_types:
                continue

            operator = subquery_types[query_id]

            if operator == Operators.NOT:
                terms.pop(0)  # First term of a NOT query cannot be redundant

            redundant_terms = []
            for term_a in terms:
                if not term_a.search_field:
                    continue
                for term_b in terms:
                    if (
                        term_a == term_b
                        or term_a in redundant_terms
                        or term_b in redundant_terms
                    ):
                        continue

                    if not term_b.search_field:
                        continue

                    field_a = term_a.search_field.value
                    field_b = term_b.search_field.value

                    if field_a != field_b:
                        continue

                    if field_a == "[mh]":
                        # excact matches required for mh
                        continue

                    if term_a.value == term_b.value or (
                        term_a.value.strip('"').lower()
                        in term_b.value.strip('"').lower().split()
                    ):
                        # Terms in AND queries follow different redundancy logic
                        # than terms in OR queries
                        if operator == Operators.AND:
                            self.add_linter_message(
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                positions=[term_a.position, term_b.position],
                                details=f"Term {term_a.value} is contained in term "
                                f"{term_b.value} and both are connected with AND. "
                                f"Therefore, term {term_b.value} is redundant.",
                            )
                            redundant_terms.append(term_a)
                        elif operator == Operators.OR:
                            self.add_linter_message(
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                positions=[term_a.position, term_b.position],
                                details=f"Term {term_b.value} is contained in term "
                                f"{term_a.value} and both are connected with OR. "
                                f"Therefore, term {term_b.value} is redundant.",
                            )
                            redundant_terms.append(term_b)

                        elif operator == Operators.NOT:
                            self.add_linter_message(
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                positions=[term_a.position, term_b.position],
                            )
                            redundant_terms.append(term_b)


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
        positions: typing.List[tuple[int, int]],
        details: str = "",
    ) -> None:
        """Add a linter message."""
        # do not add duplicates
        if any(
            error.code == msg["code"] and positions == msg["position"]
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
                "position": positions,
                "details": details,
            }
        )

    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors."""
        return any(d["is_fatal"] for e in self.messages.values() for d in e)

    def print_messages(self) -> None:
        """Print the latest linter messages."""
        if not self.messages:
            return

        for list_position, messages in self.messages.items():
            query_str = ""
            if list_position in self.parser.query_dict:
                query_str = self.parser.query_dict[list_position]["node_content"]

            for message in messages:
                code = message["code"]
                color = Colors.ORANGE

                category = ""
                if code.startswith("F"):
                    color = Colors.RED
                    category = "❌ Fatal"
                elif code.startswith("E"):
                    category = "⚠️ Error"
                elif code.startswith("W"):
                    category = "💡 Warning"

                formatted_query = format_query_string_positions(
                    query_str, message["position"], color=color
                )
                print(f"{color}{category}{Colors.END}: " f"{message['label']} ({code})")
                print(f"  {message['message']}")
                print(f"  {message['details']}")
                print(f"  {formatted_query}")
                print("\n")

    def check_status(self) -> None:
        """Check the output of the linter and report errors to the user"""

        self.print_messages()

        if self.has_fatal_errors():
            # OR any (code.is_error() for code in messages)
            # and self.parser.mode == "strict":
            raise ListQuerySyntaxError(self)
