#!/usr/bin/env python3
"""Pubmed query linter."""
import re
import typing

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import QueryErrorCode
from search_query.constants import TokenTypes
from search_query.linter_base import QueryStringLinter
from search_query.query import Query

if typing.TYPE_CHECKING:
    from search_query.parser import PubmedParser


class PubmedQueryStringLinter(QueryStringLinter):
    """Linter for PubMed Query Strings"""

    PROXIMITY_REGEX = r"^\[(.+):~(.*)\]$"
    parser: "PubmedParser"

    VALID_TOKEN_SEQUENCES: typing.Dict[TokenTypes, typing.List[TokenTypes]] = {
        TokenTypes.PARENTHESIS_OPEN: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.PARENTHESIS_CLOSED: [
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.SEARCH_TERM: [
            TokenTypes.FIELD,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.FIELD: [
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.LOGIC_OPERATOR: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
    }

    def validate_tokens(self) -> None:
        """Validate token list"""

        self.check_invalid_syntax()
        self.check_missing_tokens()
        self.check_quoted_search_terms()
        # No tokens marked as unknown token-type
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()
        self.check_character_replacement_in_search_term()
        self.check_implicit_operator()

        self.check_unsupported_pubmed_search_fields()
        self.check_general_search_field_mismatch()

        self.check_invalid_wildcard()
        self.check_invalid_proximity_operator()
        self.check_boolean_operator_readability()

    def check_implicit_operator(self) -> None:
        """Check for implicit operators in the query string"""

        for token in self.parser.tokens:
            if token.type != TokenTypes.SEARCH_TERM:
                continue

            if token.value[0] == '"' and token.value[-1] == '"':
                continue
            if " " not in token.value:
                continue
            position_of_whitespace = token.position[0] + token.value.index(" ")
            self.add_linter_message(
                QueryErrorCode.IMPLICIT_OPERATOR,
                position=token.position,
                details="Implicit operator detected. "
                f"The space at position {position_of_whitespace} "
                "will be interpreted as an AND connection. "
                "Please add an explicit operator to clarify this.",
            )

    def check_invalid_syntax(self) -> None:
        """Check for invalid syntax in the query string."""

        # Check for erroneous field syntax
        match = re.search(r"\b[A-Z]{2}=", self.parser.query_str)
        if match:
            self.add_linter_message(
                QueryErrorCode.INVALID_SYNTAX,
                position=match.span(),
                details="PubMed fields must be enclosed in brackets and "
                "after a search term, e.g. robot[TIAB] or monitor[TI]. "
                f"'{match.group(0)}' is invalid.",
            )

    def check_character_replacement_in_search_term(self) -> None:
        """Check a search term for invalid characters"""
        # https://pubmed.ncbi.nlm.nih.gov/help/
        # PubMed character conversions

        # pylint: disable=duplicate-code
        invalid_characters = "!#$%+.;<>=?\\^_{}~'()[]"
        for token in self.parser.tokens:
            if token.type != TokenTypes.SEARCH_TERM:
                continue
            value = token.value

            # Iterate over term to identify invalid characters
            # and replace them with whitespace
            for i, char in enumerate(token.value):
                if char in invalid_characters:
                    details = (
                        f"Character '{char}' in search term "
                        "will be replaced with whitespace "
                        "(see PubMed character conversions in "
                        "https://pubmed.ncbi.nlm.nih.gov/help/)"
                    )
                    self.add_linter_message(
                        QueryErrorCode.CHARACTER_REPLACEMENT,
                        position=(token.position[0] + i, token.position[0] + i + 1),
                        details=details,
                    )
                    # TBD: really change?
                    # value = value[:i] + " " + value[i + 1 :]
            # Update token
            if value != token.value:
                token.value = value

    def check_invalid_token_sequences(self) -> None:
        """Check token list for invalid token sequences."""

        # Check the first token
        if self.parser.tokens[0].type not in [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ]:
            self.add_linter_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                position=self.parser.tokens[0].position,
                details=f"Cannot start with {self.parser.tokens[0].type}",
            )

        # Check following token sequences
        for i, token in enumerate(self.parser.tokens):
            if i == 0:
                continue
            if i == len(self.parser.tokens):
                break

            token_type = token.type
            prev_type = self.parser.tokens[i - 1].type

            if token_type in self.VALID_TOKEN_SEQUENCES[prev_type]:
                continue

            details = ""
            position = (
                token.position if token_type else self.parser.tokens[i - 1].position
            )

            if token_type == TokenTypes.FIELD:
                if self.parser.tokens[i - 1].type in [TokenTypes.PARENTHESIS_CLOSED]:
                    details = "Nested queries cannot have search fields"
                else:
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

            elif token_type and prev_type and prev_type != TokenTypes.LOGIC_OPERATOR:
                details = "Missing operator"
                position = (
                    self.parser.tokens[i - 1].position[0],
                    token.position[1],
                )

            self.add_linter_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                position=position,
                details=details,
            )

        # Check the last token
        if self.parser.tokens[-1].type in [
            TokenTypes.PARENTHESIS_OPEN,
            TokenTypes.LOGIC_OPERATOR,
        ]:
            self.add_linter_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                position=self.parser.tokens[-1].position,
                details=f"Cannot end with {self.parser.tokens[-1].type}",
            )

    def check_invalid_wildcard(self) -> None:
        """Check search term for invalid wildcard *"""

        details = (
            "Wildcards cannot be used for short strings (shorter than 4 characters)."
        )
        for token in self.parser.tokens:
            if token.type != TokenTypes.SEARCH_TERM:
                continue

            if "*" not in token.value:
                continue

            if token.value == '"':
                k = 5
            else:
                k = 4
            if "*" in token.value[:k]:
                # Wildcard * is invalid
                # when applied to terms with less than 4 characters
                self.add_linter_message(
                    QueryErrorCode.INVALID_WILDCARD_USE,
                    position=token.position,
                    details=details,
                )

    def check_invalid_proximity_operator(self) -> None:
        """Check search field for invalid proximity operator"""

        for index, token in enumerate(self.parser.tokens):
            if ":~" not in token.value:
                continue
            field_token = self.parser.tokens[index]
            search_phrase_token = self.parser.tokens[index - 1]

            match = re.match(self.PROXIMITY_REGEX, field_token.value)
            if not match:
                details = f"Not matching regex {self.PROXIMITY_REGEX}"
                self.add_linter_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE,
                    position=field_token.position,
                    details=details,
                )
                continue

            field_value, prox_value = match.groups()
            field_value = "[" + field_value + "]"
            if not prox_value.isdigit():
                details = f"Proximity value '{prox_value}' is not a digit"
                self.add_linter_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE,
                    position=field_token.position,
                    details=details,
                )
                continue

            nr_of_terms = len(search_phrase_token.value.strip('"').split())
            if nr_of_terms >= 2 and not (
                search_phrase_token.value[0] == '"'
                and search_phrase_token.value[-1] == '"'
            ):
                details = (
                    "When using proximity operators, "
                    + "search terms consisting of 2 or more words "
                    + f"(i.e., {search_phrase_token.value}) "
                    + "must be enclosed in double quotes"
                )
                self.add_linter_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE,
                    position=self.parser.tokens[index - 1].position,
                    details=details,
                )

            if self.parser.map_search_field(field_value) not in {
                "[tiab]",
                Fields.TITLE,
                Fields.AFFILIATION,
            }:
                details = (
                    f"Proximity operator '{field_value}' is not supported "
                    + "for this search field (supported: [tiab], [ti], [ad])"
                )
                self.add_linter_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE,
                    position=field_token.position,
                    details=details,
                )
            # Update search field token
            self.parser.tokens[index].value = field_value

    def validate_query_tree(self, query: Query) -> None:
        """Validate the query tree"""
        # Note: search fields are not yet translated.

        self._check_redundant_terms(query)
        self._check_date_filters_in_subquery(query)
        self._check_nested_query_with_search_field(query)

    def _check_nested_query_with_search_field(self, query: Query) -> None:
        # Walk the query (its children)
        if query.operator:
            if query.search_field:
                details = (
                    "In PubMed, operators (nested queries) "
                    "cannot be used with a search field."
                )
                self.add_linter_message(
                    QueryErrorCode.NESTED_QUERY_WITH_SEARCH_FIELD,
                    position=query.position or (-1, -1),
                    details=details,
                )
            for child in query.children:
                self._check_nested_query_with_search_field(child)

    def _check_date_filters_in_subquery(self, query: Query, level: int = 0) -> None:
        """Check for date filters in subqueries"""

        # Skip top-level queries
        if level == 0:
            for child in query.children:
                self._check_date_filters_in_subquery(child, level + 1)
            return
        if query.operator:
            for child in query.children:
                self._check_date_filters_in_subquery(child, level + 1)
            return

        if query.search_field and query.search_field.value in [
            "[publication date]",
            "[pd]",
        ]:
            self.add_linter_message(
                QueryErrorCode.DATE_FILTER_IN_SUBQUERY,
                position=query.position or (-1, -1),
            )

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
                for term_b in terms:
                    if (
                        term_a == term_b
                        or term_a in redundant_terms
                        or term_b in redundant_terms
                    ):
                        continue

                    field_a = self.parser.map_search_field(term_a.search_field.value)
                    field_b = self.parser.map_search_field(term_b.search_field.value)

                    if field_a == field_b and (
                        term_a.value == term_b.value
                        or (
                            field_a != "[mh]"
                            and term_a.value.strip('"').lower()
                            in term_b.value.strip('"').lower().split()
                        )
                    ):
                        # Terms in AND queries follow different redundancy logic
                        # than terms in OR queries
                        if operator == Operators.AND:
                            self.add_linter_message(
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                position=term_a.position,
                                details=f"Term {term_a.value} is contained in term "
                                f"{term_b.value} and both are connected with AND.",
                            )
                            redundant_terms.append(term_a)
                        elif operator in {Operators.OR, Operators.NOT}:
                            self.add_linter_message(
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                position=term_b.position,
                            )
                            redundant_terms.append(term_b)

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

    def check_unsupported_pubmed_search_fields(self) -> None:
        """Check for the correct format of fields."""

        valid_fields = list(self.parser.DEFAULT_FIELD_MAP.keys()) + list(
            self.parser.DEFAULT_FIELD_MAP.values()
        )

        for token in self.parser.tokens:
            if token.type != TokenTypes.FIELD:
                continue

            t_value = token.value.lower()

            if t_value in valid_fields:
                continue

            if re.match(r"^\[[a-z\/]*\:~\d+\]$", t_value):
                continue

            self.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                position=token.position,
                details=f"Search field {token.value} at position "
                f"{token.position} is not supported.",
            )

    def check_general_search_field_mismatch(self) -> None:
        """Check general search field mismatch"""

        general_sf_parentheses = f"[{self.parser.search_field_general.lower()}]"
        if general_sf_parentheses in self.parser.DEFAULT_FIELD_MAP.values():
            general_sf = general_sf_parentheses
        elif general_sf_parentheses in self.parser.DEFAULT_FIELD_MAP:
            general_sf = self.parser.DEFAULT_FIELD_MAP[general_sf_parentheses]
        else:
            general_sf = ""

        standardized_sf_list = []
        for token in self.parser.tokens:
            if token.type != TokenTypes.FIELD:
                continue
            if (
                token.value.lower() not in self.parser.DEFAULT_FIELD_MAP
                and token.value.lower() not in self.parser.DEFAULT_FIELD_MAP.values()
            ):
                continue

            standardized_sf = token.value.lower()
            if (
                token.value.lower() in self.parser.DEFAULT_FIELD_MAP
                and token.value.lower()
            ):
                standardized_sf = self.parser.DEFAULT_FIELD_MAP[token.value.lower()]

            standardized_sf_list.append(standardized_sf)
            if general_sf and standardized_sf:
                if general_sf != standardized_sf:
                    details = (
                        "The search_field_general "
                        f"({self.parser.search_field_general}) "
                        f"and the search_field {token.value} do not match."
                    )
                    # User-provided fields and fields in the query do not match
                    self.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_CONTRADICTION,
                        position=token.position,
                        details=details,
                    )
                else:
                    details = (
                        "The search_field_general "
                        f"({self.parser.search_field_general}) "
                        f"and the search_field {token.value} are redundant."
                    )
                    # User-provided fields match fields in the query
                    self.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_REDUNDANT,
                        position=token.position,
                        details=details,
                    )

        if general_sf and not standardized_sf_list:
            # User-provided fields are missing in the query
            self.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_MISSING,
                position=(-1, -1),
                details="Search fields should be specified in the query "
                "instead of the search_field_general",
            )

        if not general_sf and not any(
            t.type == TokenTypes.FIELD for t in self.parser.tokens
        ):
            # Fields not specified
            self.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_MISSING,
                position=(-1, -1),
                details="Search field is missing (TODO: default?)",
            )
