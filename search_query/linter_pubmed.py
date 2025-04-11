#!/usr/bin/env python3
"""Pubmed query linter."""
import re
import typing

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import QueryErrorCode
from search_query.constants import TokenTypes
from search_query.parser_validation import QueryStringValidator
from search_query.query import Query
from search_query.query import SearchField

if typing.TYPE_CHECKING:
    from search_query.parser import PubmedParser


class PubmedQueryStringValidator(QueryStringValidator):
    """Class for PubMed Query String Validation"""

    PROXIMITY_REGEX = r"^\[(.+):~(.*)\]$"
    parser: "PubmedParser"

    def validate_tokens(self, tokens: list) -> list:
        """Validate token list"""
        invalid_token_indices: typing.List[int] = []

        self.check_operator()
        self._check_unbalanced_parentheses(tokens, invalid_token_indices)

        for index, token in enumerate(tokens):
            if token.type == TokenTypes.SEARCH_TERM:
                self._check_invalid_characters(index, tokens, invalid_token_indices)
                if "*" in token.value:
                    self._check_invalid_wildcard(index, tokens)
            else:
                self._check_invalid_token_position(index, tokens, invalid_token_indices)

            if (
                index not in invalid_token_indices
                and token.type == TokenTypes.FIELD
                and ":~" in token.value
            ):
                self._check_invalid_proximity_operator(index, tokens)

            if (
                index > 0
                and index not in invalid_token_indices
                and index - 1 not in invalid_token_indices
            ):
                self._check_missing_operator(index, tokens)

        refined_tokens = [
            token
            for index, token in enumerate(tokens)
            if index not in invalid_token_indices
        ]
        self._check_precedence(refined_tokens)

        return refined_tokens

    def _check_unbalanced_parentheses(
        self, tokens: list, invalid_token_indices: list
    ) -> None:
        """Check token list for unbalanced parentheses"""
        i = 0
        for index, token in enumerate(tokens):
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                i += 1
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                if i == 0:
                    # Query contains unbalanced closing parentheses
                    self.parser.add_linter_message(
                        QueryErrorCode.UNBALANCED_PARENTHESES, token.position
                    )
                    invalid_token_indices.append(index)
                else:
                    i -= 1

        if i > 0:
            # Query contains unbalanced opening parentheses
            last_index = len(tokens) - 1
            for index, token in enumerate(reversed(tokens)):
                if token.type == TokenTypes.PARENTHESIS_OPEN:
                    self.parser.add_linter_message(
                        QueryErrorCode.UNBALANCED_PARENTHESES, token.position
                    )
                    invalid_token_indices.append(last_index - index)
                    i -= 1
                if i == 0:
                    break

    def _check_precedence(self, tokens: list) -> None:
        """Check whether token list contains unspecified precedence
        (OR & AND operator in the same subquery)"""
        or_query = False
        for token in tokens:
            if token.value.upper() in {"OR", "|"}:
                or_query = True
            elif token.type in {
                TokenTypes.PARENTHESIS_OPEN,
                TokenTypes.PARENTHESIS_CLOSED,
            }:
                or_query = False
            elif token.value.upper() in {"AND", "&"} and or_query:
                self.parser.add_linter_message(
                    QueryErrorCode.IMPLICIT_PRECEDENCE, token.position
                )

    def _check_invalid_characters(
        self, index: int, tokens: list, invalid_token_indices: list
    ) -> None:
        """Check a search term for invalid characters"""

        invalid_characters = "!#$%+.;<>?\\^_{}~'()[]"

        token = tokens[index]
        value = token.value
        # Iterate over term to identify invalid characters
        # and replace them with whitespace
        for i, char in enumerate(token.value):
            if char in invalid_characters:
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_CHARACTER, token.position
                )
                value = value[:i] + " " + value[i + 1 :]
        # Update token
        if value != token.value:
            token.value = value
            if value.isspace():
                invalid_token_indices.append(index)

    def _check_invalid_wildcard(self, index: int, tokens: list) -> None:
        """Check search term for invalid wildcard *"""
        token = tokens[index]
        if token.value == '"':
            k = 5
        else:
            k = 4
        if "*" in token.value[:k]:
            # Wildcard * is invalid when applied to terms with less than 4 characters
            self.parser.add_linter_message(
                QueryErrorCode.INVALID_WILDCARD_USE, token.position
            )

    def _check_invalid_token_position(
        self, index: int, tokens: list, invalid_token_indices: list
    ) -> None:
        """Check if token list contains invalid token position at index"""
        if index == 0:
            prev_token = None
        else:
            prev_token = tokens[index - 1]

        if index == len(tokens) - 1:
            next_token = None
        else:
            next_token = tokens[index + 1]

        current_token = tokens[index]

        if current_token.type == TokenTypes.PARENTHESIS_OPEN:
            if next_token and next_token.type == TokenTypes.PARENTHESIS_CLOSED:
                self.parser.add_linter_message(
                    QueryErrorCode.EMPTY_PARENTHESES,
                    (current_token.position[0], next_token.position[1]),
                )
                invalid_token_indices.append(index)
                invalid_token_indices.append(index + 1)

        if current_token.type == TokenTypes.LOGIC_OPERATOR:
            if not (
                prev_token
                and (
                    prev_token.type
                    in [
                        TokenTypes.SEARCH_TERM,
                        TokenTypes.FIELD,
                        TokenTypes.PARENTHESIS_CLOSED,
                    ]
                )
            ):
                # Invalid operator position
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_OPERATOR_POSITION, current_token.position
                )
                invalid_token_indices.append(index)
            elif not (
                next_token
                and (
                    next_token.type
                    in {TokenTypes.PARENTHESIS_OPEN, TokenTypes.SEARCH_TERM}
                )
            ):
                # Invalid operator position
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_OPERATOR_POSITION, current_token.position
                )
                invalid_token_indices.append(index)

        elif current_token.type == TokenTypes.FIELD:
            if not (prev_token and prev_token.type == TokenTypes.SEARCH_TERM):
                # Invalid search field position
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_SEARCH_FIELD_POSITION, current_token.position
                )
                invalid_token_indices.append(index)

    def _check_invalid_proximity_operator(self, index: int, tokens: list) -> None:
        """Check search field for invalid proximity operator"""
        field_token = tokens[index]
        search_phrase_token = tokens[index - 1]

        match = re.match(self.PROXIMITY_REGEX, field_token.value)
        if match:
            field_value, prox_value = match.groups()
            field_value = "[" + field_value + "]"
            if not prox_value.isdigit():
                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE, field_token.position
                )
            else:
                nr_of_terms = len(search_phrase_token.value.strip('"').split())
                if not (
                    search_phrase_token.value[0] == '"'
                    and search_phrase_token.value[-1] == '"'
                    and nr_of_terms >= 2
                ):
                    self.parser.add_linter_message(
                        QueryErrorCode.INVALID_PROXIMITY_USE, field_token.position
                    )

                if self.parser.map_search_field(field_value) not in {
                    "tiab",
                    Fields.TITLE,
                    Fields.AFFILIATION,
                }:
                    self.parser.add_linter_message(
                        QueryErrorCode.INVALID_PROXIMITY_USE, field_token.position
                    )

            # Update search field token
            tokens[index].value = field_value
        else:
            self.parser.add_linter_message(
                QueryErrorCode.INVALID_PROXIMITY_USE, field_token.position
            )

    def _check_missing_operator(self, index: int, tokens: list) -> None:
        """Check if there is a missing operator between previous and current token"""
        token_1 = tokens[index - 1]
        token_2 = tokens[index]
        if token_1.type in {
            TokenTypes.PARENTHESIS_CLOSED,
            TokenTypes.SEARCH_TERM,
            TokenTypes.FIELD,
        } and token_2.type in {TokenTypes.PARENTHESIS_OPEN, TokenTypes.SEARCH_TERM}:
            self.parser.add_linter_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE_MISSING_OPERATOR,
                (token_1.position[0], token_2.position[1]),
            )

    def validate_query_tree(self, query: Query) -> None:
        """Validate the query tree"""
        self._check_nested_not_query(query)
        self._check_redundant_terms(query)

    def _check_nested_not_query(self, query: Query) -> None:
        """Check query tree for nested NOT queries"""
        for child in query.children:
            if child.operator and child.value == Operators.NOT:
                self.parser.add_linter_message(
                    QueryErrorCode.NESTED_NOT_QUERY, pos=child.position or (-1, -1)
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

                    field_value_1 = self.parser.map_search_field(
                        term_a.search_field.value
                    )
                    field_value_2 = self.parser.map_search_field(
                        term_b.search_field.value
                    )

                    if field_value_1 == field_value_2 and (
                        term_a.value == term_b.value
                        or (
                            field_value_1 != "[mh]"
                            and term_a.value.strip('"').lower()
                            in term_b.value.strip('"').lower().split()
                        )
                    ):
                        # Terms in AND queries follow different redundancy logic
                        # than terms in OR queries
                        if operator == Operators.AND:
                            self.parser.add_linter_message(
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                term_a.position,
                            )
                            redundant_terms.append(term_a)
                        elif operator in {Operators.OR, Operators.NOT}:
                            self.parser.add_linter_message(
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                term_b.position,
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

    def validate_search_fields(self, query: Query, user_field_values: list) -> None:
        """Validate search terms and fields"""
        leaf_queries = self.parser.get_query_leaves(query)

        for leaf_query in leaf_queries:
            self._check_unsupported_search_field(leaf_query.search_field)

        query_field_values = [
            q.search_field.value
            for q in leaf_queries
            if not (q.search_field.value == "all" and not q.search_field.position)
        ]
        self._check_search_field_alignment(
            set(query_field_values), set(user_field_values)
        )

    def _check_unsupported_search_field(self, search_field: SearchField) -> None:
        """Check unsupported search field"""

        if search_field.value not in Fields.all() or (
            search_field.position and search_field.value == "ab"
        ):
            self.parser.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_UNSUPPORTED, search_field.position
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
                self.parser.add_linter_message(
                    QueryErrorCode.SEARCH_FIELD_CONTRADICTION, None
                )
            else:
                # User-provided fields match fields in the query
                self.parser.add_linter_message(
                    QueryErrorCode.SEARCH_FIELD_REDUNDANT, None
                )

        elif user_field_values and not query_field_values:
            # User-provided fields are missing in the query
            self.parser.add_linter_message(QueryErrorCode.SEARCH_FIELD_MISSING, None)

        elif not user_field_values and not query_field_values:
            # Fields not specified
            self.parser.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_NOT_SPECIFIED, None
            )
