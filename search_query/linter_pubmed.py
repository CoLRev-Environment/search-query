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
from search_query.query import SearchField

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

        self.check_missing_tokens()
        # No tokens marked as unknown token-type
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()
        self.check_character_replacement_in_search_term()

        self.check_invalid_wildcard()
        self.check_invalid_proximity_operator()
        self.check_boolean_operator_readability()

    def check_character_replacement_in_search_term(self) -> None:
        """Check a search term for invalid characters"""
        # https://pubmed.ncbi.nlm.nih.gov/help/
        # PubMed character conversions

        invalid_characters = "!#$%+.;<>?\\^_{}~'()[]"
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
                    value = value[:i] + " " + value[i + 1 :]
            # Update token
            if value != token.value:
                token.value = value

    def check_invalid_token_sequences(self) -> None:
        """Check token list for invalid token sequences."""
        for i, token in enumerate(self.parser.tokens):
            # Check the last token
            if i == len(self.parser.tokens):
                if self.parser.tokens[i - 1].type in [
                    TokenTypes.PARENTHESIS_OPEN,
                    TokenTypes.LOGIC_OPERATOR,
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

    def check_invalid_wildcard(self) -> None:
        """Check search term for invalid wildcard *"""

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
                    QueryErrorCode.INVALID_WILDCARD_USE, position=token.position
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
            print(search_phrase_token)
            print(search_phrase_token.value.strip('"').split())
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
                    position=field_token.position,
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
        self._check_nested_not_query(query)
        self._check_redundant_terms(query)
        self._check_date_filters_in_subquery(query)

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

        # TODO : extend for variations...
        if query.search_field and query.search_field.value in ["[publication date]"]:
            self.add_linter_message(
                QueryErrorCode.DATE_FILTER_IN_SUBQUERY,
                position=query.position or (-1, -1),
            )

    def _check_nested_not_query(self, query: Query) -> None:
        """Check query tree for nested NOT queries"""
        for child in query.children:
            if child.operator and child.value == Operators.NOT:
                self.add_linter_message(
                    QueryErrorCode.NESTED_NOT_QUERY, position=child.position or (-1, -1)
                )
            self._check_nested_not_query(child)

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

    def validate_search_fields(self, query: Query) -> None:
        """Validate search terms and fields"""

        leaf_queries = self.parser.get_query_leaves(query)

        for leaf_query in leaf_queries:
            self._check_unsupported_search_field(leaf_query.search_field)

        query_field_values = [
            q.search_field.value
            for q in leaf_queries
            if not (q.search_field.value == "all" and not q.search_field.position)
        ]
        user_field_values = self.parser.parse_user_provided_fields(
            self.parser.search_field_general
        )
        if user_field_values:
            self._check_search_field_alignment(
                set(query_field_values), set(user_field_values)
            )

    def _check_unsupported_search_field(self, search_field: SearchField) -> None:
        """Check unsupported search field"""

        if search_field.value not in Fields.all() or (
            search_field.position and search_field.value == "ab"
        ):
            self.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                position=search_field.position or (-1, -1),
            )
            search_field.value = Fields.ALL
            search_field.position = None

    def _check_search_field_alignment(
        self, query_field_values: set, user_field_values: set
    ) -> None:
        """Compare user-provided fields with the fields found in query string"""
        if user_field_values and query_field_values:
            if user_field_values != query_field_values:
                # User-provided fields and fields in the query do not match
                self.add_linter_message(
                    QueryErrorCode.SEARCH_FIELD_CONTRADICTION, position=(-1, -1)
                )
            else:
                # User-provided fields match fields in the query
                self.add_linter_message(
                    QueryErrorCode.SEARCH_FIELD_REDUNDANT, position=(-1, -1)
                )

        elif user_field_values and not query_field_values:
            # User-provided fields are missing in the query
            self.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_MISSING, position=(-1, -1)
            )

        elif not user_field_values and not query_field_values:
            # Fields not specified
            self.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_MISSING, position=(-1, -1)
            )
