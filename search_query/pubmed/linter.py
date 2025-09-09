#!/usr/bin/env python3
"""Pubmed query linter."""
from __future__ import annotations

import re
import typing

from search_query.constants import Colors
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.linter_base import QueryListLinter
from search_query.linter_base import QueryStringLinter
from search_query.pubmed.constants import map_to_standard
from search_query.pubmed.constants import PROXIMITY_SEARCH_REGEX
from search_query.pubmed.constants import syntax_str_to_generic_field_set
from search_query.pubmed.constants import YEAR_PUBLISHED_FIELD_REGEX

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.pubmed.parser import PubmedListParser
    from search_query.parser_base import QueryStringParser
    from search_query.query import Query


# pylint: disable=duplicate-code


class PubmedQueryStringLinter(QueryStringLinter):
    """Linter for PubMed Query Strings"""

    PROXIMITY_REGEX = re.compile(r"^\[(.+):~(.*)\]$")
    PLATFORM: PLATFORM = PLATFORM.PUBMED

    VALID_TOKEN_SEQUENCES: typing.Dict[TokenTypes, typing.List[TokenTypes]] = {
        TokenTypes.PARENTHESIS_OPEN: [
            TokenTypes.TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.PARENTHESIS_CLOSED: [
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.TERM: [
            TokenTypes.FIELD,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.FIELD: [
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
            TokenTypes.RANGE_OPERATOR,
        ],
        TokenTypes.LOGIC_OPERATOR: [
            TokenTypes.TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.RANGE_OPERATOR: [
            TokenTypes.TERM,
        ],
    }

    YEAR_VALUE_REGEX = re.compile(
        r'^"?'
        r"(?P<year>\d{4})"
        r"(?P<month>\/(0[1-9]|1[0-2]))?"
        r"(?P<day>\/(0[1-9]|[12]\d|3[01]))?"
        r"(\:"
        r"(?P<year2>(\d{4})"
        r"(?P<month2>\/(0[1-9]|1[0-2]))?"
        r"(?P<day2>\/(0[1-9]|[12]\d|3[01]))?))?"
        r'"?$',
        re.VERBOSE,
    )

    def __init__(
        self,
        query_str: str = "",
        *,
        original_str: typing.Optional[str] = None,
        silent: bool = False,
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_str=query_str,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )

    def validate_tokens(
        self,
        *,
        tokens: typing.List[Token],
        query_str: str,
        field_general: str = "",
    ) -> typing.List[Token]:
        """Validate token list"""

        self.tokens = tokens
        self.query_str = query_str
        self.field_general = field_general

        self.check_invalid_syntax()
        self.check_missing_tokens()

        # No tokens marked as unknown token-type
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()
        if self.has_fatal_errors():
            return self.tokens

        self.check_unsupported_pubmed_fields()
        self.check_general_field()
        self.check_implicit_fields()
        self.check_boolean_operator_readability()

        self.check_invalid_proximity_operator()
        return self.tokens

    def check_invalid_syntax(self) -> None:
        """Check for invalid syntax in the query string."""

        # Check for erroneous field syntax
        match = re.search(r"\b[A-Z]{2}=", self.query_str)
        if match:
            self.add_message(
                QueryErrorCode.INVALID_SYNTAX,
                positions=[match.span()],
                details="PubMed fields must be enclosed in brackets and "
                "after a search term, e.g. robot[TIAB] or monitor[TI]. "
                f"'{match.group(0)}' is invalid.",
                fatal=True,
            )

    def check_character_replacement_in_term(self, query: Query) -> None:
        """Check a search term for invalid characters"""
        # https://pubmed.ncbi.nlm.nih.gov/help/
        # PubMed character conversions
        # pylint: disable=duplicate-code
        invalid_characters = "!#$%+.;<>=?\\^_{}~'()[]"

        if query.is_term():
            # Iterate over term to identify invalid characters
            # and replace them with whitespace
            for i, char in enumerate(query.value):
                if char in invalid_characters:
                    details = (
                        f"Character '{char}' in search term "
                        "will be replaced with whitespace.\n"
                        "See PubMed character conversions: "
                        "https://pubmed.ncbi.nlm.nih.gov/help/)"
                    )
                    positions = [(-1, -1)]
                    if query.position:
                        positions = [(query.position[0] + i, query.position[0] + i + 1)]
                    self.add_message(
                        QueryErrorCode.CHARACTER_REPLACEMENT,
                        positions=positions,
                        details=details,
                    )

        for child in query.children:
            self.check_character_replacement_in_term(child)

    def check_invalid_token_sequences(self) -> None:
        """Check token list for invalid token sequences."""

        # Check the first token
        if self.tokens[0].type not in [
            TokenTypes.TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ]:
            self.add_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                positions=[self.tokens[0].position],
                details=f"Cannot start with {self.tokens[0].type.value}",
                fatal=True,
            )

        # pylint: disable=duplicate-code
        # Check following token sequences
        for i, token in enumerate(self.tokens):
            if i == 0:
                continue

            token_type = token.type
            prev_type = self.tokens[i - 1].type

            if token_type in self.VALID_TOKEN_SEQUENCES[prev_type]:
                continue

            details = ""
            positions = [token.position if token_type else self.tokens[i - 1].position]

            if token_type == TokenTypes.FIELD:
                if self.tokens[i - 1].type in [TokenTypes.PARENTHESIS_CLOSED]:
                    details = "Nested queries cannot have search fields"
                else:
                    details = "Invalid search field position"
                positions = [
                    (
                        self.tokens[i - 1].position[0],
                        token.position[1],
                    )
                ]

            elif token_type == TokenTypes.LOGIC_OPERATOR:
                details = "Invalid operator position"
                positions = [
                    (
                        self.tokens[i - 1].position[0],
                        token.position[1],
                    )
                ]

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

            elif (
                token_type
                and prev_type
                and prev_type not in [TokenTypes.LOGIC_OPERATOR]
            ):
                details = (
                    "Missing operator between "
                    f'"{self.tokens[i - 1].value} {token.value}"'
                )
                positions = [
                    (
                        self.tokens[i - 1].position[0],
                        token.position[1],
                    )
                ]

            self.add_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                positions=positions,
                details=details,
                fatal=True,
            )

        # Check the last token
        if self.tokens[-1].type in [
            TokenTypes.PARENTHESIS_OPEN,
            TokenTypes.LOGIC_OPERATOR,
        ]:
            self.add_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                positions=[self.tokens[-1].position],
                details=f"Cannot end with {self.tokens[-1].type.value}",
                fatal=True,
            )

    def _print_unequal_precedence_warning(self, index: int) -> None:
        unequal_precedence_operators = self._get_unequal_precedence_operators(
            self.tokens[index:]
        )
        if not unequal_precedence_operators:
            return

        precedence_list = [o.value for o in unequal_precedence_operators]
        precedence_lines = []
        for idx, op in enumerate(precedence_list):
            if idx == 0:
                precedence_lines.append(
                    f"- {Colors.ORANGE}{op}{Colors.END} "
                    f"is evaluated first "
                    f"because it is the leftmost operator"
                )
            elif idx == len(precedence_list) - 1:
                precedence_lines.append(
                    f"- {Colors.ORANGE}{op}{Colors.END} "
                    f"is evaluated last "
                    f"because it is the rightmost operator"
                )
            else:
                precedence_lines.append(
                    f"- {Colors.ORANGE}{op}{Colors.END} " f"is evaluated next"
                )

        precedence_info = "\n".join(precedence_lines)

        details = (
            "The query uses multiple operators, but without parentheses "
            "to make the\nintended logic explicit. PubMed evaluates queries "
            "strictly from left to\nright without applying traditional "
            "operator precedence. This can lead to\nunexpected "
            "interpretations of the query.\n\n"
            "Specifically:\n"
            f"{precedence_info}\n\n"
            "To fix this, search-query adds artificial parentheses around\noperators "
            "based on their left-to-right position in the query.\n\n"
        )

        self.add_message(
            QueryErrorCode.IMPLICIT_PRECEDENCE,
            positions=[o.position for o in unequal_precedence_operators],
            details=details,
        )

    def add_artificial_parentheses_for_operator_precedence(
        self,
        index: int = 0,
        output: typing.Optional[list] = None,
    ) -> tuple[int, list[Token]]:
        """
        Adds artificial parentheses with position (-1, -1)
        to enforce PubMed operator precedence.
        """
        if output is None:
            output = []
        # Value of operator
        value = 0
        # Value of previous operator
        previous_value = -1
        # Added artificial parentheses
        art_par = 0
        # Start index
        start_index = index

        self._print_unequal_precedence_warning(index)

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
                # Add opening parentheses in case there are missing ones
                if art_par < 0:
                    while art_par < 0:
                        output.insert(
                            start_index,
                            Token(
                                value="(",
                                type=TokenTypes.PARENTHESIS_OPEN,
                                position=(-1, -1),
                            ),
                        )
                        art_par += 1
                return index, output

            if self.tokens[index].type in [
                TokenTypes.LOGIC_OPERATOR,
                TokenTypes.PROXIMITY_OPERATOR,
            ]:
                value = self.get_precedence(self.tokens[index].value.upper())

                if previous_value in (value, -1):
                    # Same precedence → just add to output
                    output.append(self.tokens[index])
                    previous_value = value

                elif value != previous_value:
                    # Different precedence → close parenthesis
                    output.append(
                        Token(
                            value=")",
                            type=TokenTypes.PARENTHESIS_CLOSED,
                            position=(-1, -1),
                        )
                    )
                    previous_value -= 1
                    art_par -= 1
                    output.append(self.tokens[index])
                    previous_value = value

                index += 1
                continue

            # Default: search terms, fields, etc.
            output.append(self.tokens[index])
            index += 1

        # Add opening parentheses in case there are missing ones
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

    def check_invalid_wildcard(self, query: Query) -> None:
        """Check search term for invalid wildcard *"""

        details = (
            "Wildcards cannot be used for short strings (shorter than 4 characters)."
        )
        if query.is_term():
            if "*" not in query.value:
                return

            if query.value[0] == '"':
                k = 5
            else:
                k = 4
            if "*" in query.value[:k]:
                # Wildcard * is invalid
                # when applied to terms with less than 4 characters
                self.add_message(
                    QueryErrorCode.INVALID_WILDCARD_USE,
                    positions=[query.position] if query.position else [],
                    details=details,
                )

        for child in query.children:
            self.check_invalid_wildcard(child)

    def check_invalid_proximity_operator(self) -> None:
        """Check search field for invalid proximity operator"""

        for index, token in enumerate(self.tokens):
            if ":~" not in token.value:
                continue
            field_token = self.tokens[index]
            search_phrase_token = self.tokens[index - 1]

            match = self.PROXIMITY_REGEX.match(field_token.value)
            assert match
            field_value, prox_value = match.groups()
            field_value = "[" + field_value + "]"
            if not prox_value.isdigit():
                details = (
                    f"Proximity value '{prox_value}' is not a digit. "
                    "Using default 3 instead."
                )
                self.add_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE,
                    positions=[field_token.position],
                    details=details,
                )
                continue

            nr_of_terms = len(search_phrase_token.value.strip('"').split())
            if nr_of_terms < 2 or not (
                search_phrase_token.value[0] == '"'
                and search_phrase_token.value[-1] == '"'
            ):
                details = (
                    "Proximity search requires 2 or "
                    "more search terms enclosed in double quotes."
                )
                self.add_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE,
                    positions=[self.tokens[index - 1].position],
                    details=details,
                )

            if map_to_standard(field_value) not in {
                "[tiab]",
                "[ti]",
                "[ad]",
            }:
                details = (
                    f"Proximity operator is not supported: '{field_token.value}'"
                    + " (supported search fields: [tiab], [ti], [ad])"
                )
                self.add_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE,
                    positions=[field_token.position],
                    details=details,
                )

    def check_year_format(self, query: Query) -> None:
        """Check for the correct format of year."""

        if query.is_term():
            if not query.field:
                return

            if not YEAR_PUBLISHED_FIELD_REGEX.match(query.field.value):
                return

            if not self.YEAR_VALUE_REGEX.match(query.value):
                self.add_message(
                    QueryErrorCode.YEAR_FORMAT_INVALID,
                    positions=[query.position] if query.position else [],
                    fatal=True,
                )
                return

        for child in query.children:
            self.check_year_format(child)

    def validate_query_tree(self, query: Query) -> None:
        """Validate the query tree"""
        # Note: search fields are not yet translated.

        self.check_invalid_wildcard(query)

        self.check_unbalanced_quotes_in_terms(query)
        self.check_character_replacement_in_term(query)

        self.check_operators_with_fields(query)
        self._check_unnecessary_nesting(query)
        self.check_year_format(query)

        term_field_query = self.get_query_with_fields_at_terms(query)
        self._check_date_filters_in_subquery(term_field_query)
        self._check_journal_filters_in_subquery(term_field_query)
        self._check_redundant_terms(term_field_query)
        self._check_for_wildcard_usage(term_field_query)
        # mh is not matched exactly, terms can be redundant:
        # https://pubmed.ncbi.nlm.nih.gov/31176308/
        # is found by both searches:
        # "Sleep"[mh] AND "vigilant attention"[ti]
        # "Sleep Deprivation"[mh] AND "vigilant attention"[ti]

    def validate_platform_query(self, query: Query) -> None:
        """Validate the query for the PubMed platform"""

        term_field_query = self.get_query_with_fields_at_terms(query)
        self._check_for_opportunities_to_combine_subqueries(term_field_query)

    def syntax_str_to_generic_field_set(self, field_value: str) -> set:
        """Translate a search field"""

        return syntax_str_to_generic_field_set(field_value)

    # pylint: disable=duplicate-code
    def check_unsupported_pubmed_fields(self) -> None:
        """Check for the correct format of fields."""

        for token in self.tokens:
            if token.type != TokenTypes.FIELD:
                continue

            if PROXIMITY_SEARCH_REGEX.match(token.value):
                continue
            try:
                map_to_standard(token.value)
            except ValueError:
                if ":~" in token.value:
                    # Will be handled in check_invalid_proximity_operator
                    return
                self.add_message(
                    QueryErrorCode.FIELD_UNSUPPORTED,
                    positions=[token.position],
                    details=f"Search field {token.value} is not supported.",
                    fatal=True,
                )

    def check_implicit_fields(self) -> None:
        """Check the general search field"""

        # search fields are required for each term.
        # otherwise, pubmed implicitly sets [all]

        implicit_positions = []
        for i, _ in enumerate(self.tokens):
            token_type = self.tokens[i].type
            next_token_type = TokenTypes.TERM  # Default
            if i < len(self.tokens) - 1:
                next_token_type = self.tokens[i + 1].type
            if token_type == TokenTypes.TERM and next_token_type != TokenTypes.FIELD:
                implicit_positions.append(self.tokens[i].position)

        if implicit_positions:
            details = "The search field is implicit (will be set to [all] by PubMed)."
            self.add_message(
                QueryErrorCode.FIELD_IMPLICIT,
                positions=implicit_positions,
                details=details,
            )


class PubmedQueryListLinter(QueryListLinter):
    """Linter for PubMed Query Strings"""

    OPERATOR_NODE_REGEX = re.compile(r"#?\d+|AND|OR|NOT")

    def __init__(
        self,
        parser: PubmedListParser,
        string_parser_class: typing.Type[QueryStringParser],
        ignore_failing_linter: bool = False,
    ) -> None:
        self.parser: PubmedListParser = parser
        self.string_parser_class = string_parser_class
        super().__init__(
            parser,
            string_parser_class,
            ignore_failing_linter=ignore_failing_linter,
        )

    def validate_tokens(self) -> None:
        """Validate token list"""

        self._check_list_query_invalid_reference()

    def _check_list_query_invalid_reference(self) -> None:
        # check if all list-references exist
        for ind, query_node in self.parser.query_dict.items():
            # check if all list references exist
            for match in re.finditer(
                self.parser.LIST_ITEM_REFERENCE,
                str(query_node["node_content"]),
            ):
                reference = match.group()
                position = match.span()
                offset = query_node["content_pos"][0]
                position = (position[0] + offset, position[1] + offset)
                if reference.replace("#", "") not in self.parser.query_dict:
                    self.add_message(
                        QueryErrorCode.LIST_QUERY_INVALID_REFERENCE,
                        list_position=ind,
                        positions=[position],
                        details=f"List reference {reference} not found.",
                        fatal=True,
                    )
