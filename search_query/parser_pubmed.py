#!/usr/bin/env python3
"""Pubmed query parser."""
import re
import typing

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import PubmedErrorCodes
from search_query.exception import PubmedFieldMismatch
from search_query.exception import PubmedFieldWarning
from search_query.exception import PubmedInvalidFieldTag
from search_query.exception import PubmedQueryWarning
from search_query.exception import QuerySyntaxError
from search_query.exception import SearchQueryException
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class PubmedParser(QueryStringParser):
    """Parser for Pubmed queries."""

    search_fields = ""
    silence_warnings = False

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.PUBMED]

    DEFAULT_FIELD_MAP = {
        "[affiliation]": "[ad]",
        "[all fields]": "[all]",
        "[article identifier]": "[aid]",
        "[author]": "[au]",
        "[author identifier]": "[auid]",
        "[completion date]": "[dcom]",
        "[conflict of interest statement]": "[cois]",
        "[corporate author]": "[cn]",
        "[create date]": "[crdt]",
        "[ec/rn number]": "[rn]",
        "[editor]": "[ed]",
        "[entry date]": "[edat]",
        "[filter]": "[sb]",
        "[first author name]": "[1au]",
        "[full author name]": "[fau]",
        "[full investigator name]": "[fir]",
        "[grants and funding]": "[gr]",
        "[investigator]": "[ir]",
        "[isbn]": "[isbn]",
        "[issue]": "[ip]",
        "[journal]": "[ta]",
        "[language]": "[la]",
        "[last author name]": "[lastau]",
        "[location id]": "[lid]",
        "[mesh date]": "[mhda]",
        "[mesh]": "[mh]",
        "[mesh terms]": "[mh]",
        "[mesh terms:noexp]": "[mh]",
        "[mh:noexp]": "[mh]",
        "[mesh:noexp]": "[mh]",
        "[mesh major topic]": "[mh]",
        "[majr]": "[mh]",
        "[mj]": "[mh]",
        "[mesh subheading]": "[mh]",
        "[subheading]": "[mh]",
        "[sh]": "[mh]",
        "[modification date]": "[lr]",
        "[nlm unique id]": "[jid]",
        "[other term]": "[ot]",
        "[pagination]": "[pg]",
        "[personal name as subject]": "[ps]",
        "[pharmacological action]": "[pa]",
        "[place of publication]": "[pl]",
        "[publication date]": "[dp]",
        "[publication type]": "[pt]",
        "[publisher]": "[pubn]",
        "[secondary source id]": "[si]",
        "[subset]": "[sb]",
        "[supplementary concept]": "[nm]",
        "[text word]": "[tw]",
        "[title]": "[ti]",
        "[title/abstract]": "[tiab]",
        "[transliterated title]": "[tt]",
        "[volume]": "[vi]",
    }

    DEFAULT_ERROR_MESSAGES = {
        # Fatal
        PubmedErrorCodes.UNBALANCED_PARENTHESES: "Unbalanced parentheses.",
        PubmedErrorCodes.MISSING_OPERATOR: "Boolean operator expected.",
        PubmedErrorCodes.INVALID_BRACKET_USE: "Invalid use of square brackets.",
        PubmedErrorCodes.INVALID_OPERATOR_POSITION: "Invalid operator position.",
        PubmedErrorCodes.INVALID_FIELD_POSITION: "Search field tags should directly follow search terms.",
        PubmedErrorCodes.EMPTY_PARENTHESES: "Empty parentheses.",
        PubmedErrorCodes.NESTED_NOT_QUERY: "NOT operator should not be nested inside a subquery.",
        # Error
        PubmedErrorCodes.INVALID_PROXIMITY_SYNTAX: "Invalid proximity syntax.",
        PubmedErrorCodes.INVALID_PROXIMITY_DISTANCE: "Invalid proximity distance. Proximity distance should be a positive integer.",
        PubmedErrorCodes.INVALID_PROXIMITY_USE: "Invalid proximity use.",
        PubmedErrorCodes.FIELD_CONTRADICTION: "Search fields in search string do not match the user-provided fields:",
        PubmedErrorCodes.MISSING_QUERY_FIELD: "User-provided search fields missing in search string:",
        PubmedErrorCodes.UNSUPPORTED_FIELD: "Field tag unsupported by the PubMed search interface: https://pubmed.ncbi.nlm.nih.gov/help/#search-tags.",
        PubmedErrorCodes.INVALID_CHARACTER: "Search term contains invalid character:",
        PubmedErrorCodes.INVALID_WILDCARD: "Invalid wildcard use. Search terms must have at least 4 characters before the first wildcard *.",
        # Warning
        PubmedErrorCodes.FIELD_REDUNDANT: "Warning: User-provided search fields are redundant. "
        "To avoid redundancy, it is recommended to specify search field tags in the search string only.",
        PubmedErrorCodes.FIELD_NOT_SPECIFIED: "Warning: Search fields not specified. "
        "If applicable, it is recommended to explicitly define search fields in the search string.",
        PubmedErrorCodes.TERM_REDUNDANT: "Warning: Redundant search term. "
        "To avoid an unnecessarily complex query structure, it is recommended to remove redundant search terms.",
        PubmedErrorCodes.PRECEDENCE_WARNING: "Warning: AND operator used after OR operator in the same subquery. "
        "PubMed does not enforce operator precedence and processes queries strictly from left to right.",
    }

    # Messages to inform the user about automatic corrections made by the parser when operating in non-strict mode.
    NON_STRICT_CORRECTION_MESSAGES = {
        PubmedErrorCodes.INVALID_PROXIMITY_SYNTAX: "Proximity operator has been ignored.",
        PubmedErrorCodes.INVALID_PROXIMITY_DISTANCE: "Proximity operator has been ignored.",
        PubmedErrorCodes.INVALID_PROXIMITY_USE: "Proximity operator has been ignored.",
        PubmedErrorCodes.UNSUPPORTED_FIELD: "Field has been converted to default field [all].",
        PubmedErrorCodes.INVALID_CHARACTER: "Character has been converted to whitespace.",
        PubmedErrorCodes.INVALID_WILDCARD: "Wildcard * has been ignored.",
    }

    SEARCH_FIELD_REGEX = r"\[[^\[]*?\]"
    OPERATOR_REGEX = r"(\||&|\b(?:AND|OR|NOT)\b)(?!\s?\[[^\[]*?\])"
    PARENTHESIS_REGEX = r"[\(\)]"
    SEARCH_PHRASE_REGEX = r"\".*?\""
    PROXIMITY_REGEX = r"^\[(.+):~(.*)\]$"

    pattern = "|".join(
        [SEARCH_FIELD_REGEX, OPERATOR_REGEX, PARENTHESIS_REGEX, SEARCH_PHRASE_REGEX]
    )

    def tokenize(self) -> None:
        """Tokenize the query_str"""
        # Parse tokens and positions based on regex patterns.
        tokens = re.finditer(
            pattern=self.pattern, string=self.query_str, flags=re.IGNORECASE
        )

        # Add tokens along with their positions.
        prev_token_end_pos = 0
        for token in tokens:
            current_token_start_pos = token.span()[0]
            current_token_end_pos = token.span()[1]

            # Gaps between quoted search phrases, operators, fields and parentheses are the unquoted search terms.
            if current_token_start_pos > prev_token_end_pos:
                self._add_token(prev_token_end_pos, current_token_start_pos)

            self._add_token(current_token_start_pos, current_token_end_pos)
            prev_token_end_pos = current_token_end_pos

        if len(self.query_str) > prev_token_end_pos:
            self._add_token(prev_token_end_pos, len(self.query_str))

    def _add_token(self, start_pos: int, end_pos: int) -> None:
        """Add token to list"""
        token_value = self.query_str[start_pos:end_pos]

        if self.is_term(token_value):
            # Filter out tokens consisting only of whitespace.
            if token_value.isspace():
                return

            # Remove leading and trailing whitespace and update start/end positions accordingly.
            token_value_stripped = token_value.strip()
            start_pos += len(token_value) - len(token_value.lstrip())
            end_pos -= len(token_value) - len(token_value.rstrip())

            token_value = token_value_stripped

        self.tokens.append((token_value, (start_pos, end_pos)))

    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return bool(re.match(r"^\[.*]$", token))

    def is_operator(self, token: str) -> bool:
        """Token is operator"""
        return bool(re.match(r"^(&|\||AND|OR|NOT)$", token, re.IGNORECASE))

    def get_operator_type(self, operator: str) -> str:
        """Get operator type"""
        if operator.upper() in {"&", "AND"}:
            return Operators.AND
        elif operator.upper() in {"|", "OR"}:
            return Operators.OR
        elif operator.upper() == "NOT":
            return Operators.NOT
        else:
            return ""

    def parse_query_tree(self, tokens: list) -> Query:
        """Parse a query from a list of tokens"""

        if self.is_compound_query(tokens):
            query = self._parse_compound_query(tokens)

        elif self.is_nested_query(tokens):
            query = self._parse_nested_query(tokens)

        elif self.is_term_query(tokens):
            query = self._parse_search_term(tokens)

        else:
            raise ValueError()

        return query

    def is_term_query(self, tokens):
        return self.is_term(tokens[0][0]) and len(tokens) == 1

    def is_compound_query(self, tokens):
        return bool(self._get_operator_indices(tokens))

    def is_nested_query(self, tokens):
        return tokens[0][0] == "(" and tokens[-1][0] == ")"

    def _get_operator_indices(self, tokens: list) -> list:
        """Get indices of top-level operators in the token list"""
        operator_indices = []

        i = 0
        first_operator_found = False
        first_operator = ""
        # Iterate over tokens in reverse to find and save positions of consecutive top-level operators
        # matching the first encountered until a different type is found.
        for token in reversed(tokens):
            token_value = token[0]
            token_index = tokens.index(token)

            if token_value == "(":
                i = i + 1
            elif token_value == ")":
                i = i - 1

            if i == 0 and self.is_operator(token_value):
                operator = self.get_operator_type(token_value)
                if not first_operator_found:
                    first_operator = operator
                    first_operator_found = True
                if operator == first_operator:
                    operator_indices.append(token_index)
                else:
                    break

        return operator_indices

    def _parse_compound_query(self, tokens: list) -> Query:
        """Parse a compound query consisting of two or more subqueries connected by a boolean operator"""

        operator_indices = self._get_operator_indices(tokens)

        # Divide tokens into separate lists based on top-level operator positions.
        token_lists = []
        i = 0
        for position in reversed(operator_indices):
            token_lists.append(tokens[i:position])
            i = position + 1
        token_lists.append(tokens[i:])

        # The token lists represent the subqueries (children) of the compound query and are parsed individually.
        children = []
        for token_list in token_lists:
            query = self.parse_query_tree(token_list)
            children.append(query)

        # TODO : assert operators equal?
        operator_type = self.get_operator_type(tokens[operator_indices[0]][0])

        query_start_pos = tokens[0][1][0]
        query_end_pos = tokens[-1][1][1]

        return Query(
            value=operator_type,
            operator=True,
            search_field=SearchField(value=Fields.ALL),
            children=children,
            position=(query_start_pos, query_end_pos),
        )

    def _parse_nested_query(self, tokens: list) -> Query:
        """Parse a query nested inside a pair of parentheses"""
        inner_query = self.parse_query_tree(tokens[1:-1])
        return inner_query

    def _parse_search_term(self, tokens: list) -> Query:
        """Parse a search term"""
        search_term = tokens[0]
        query_start_pos = tokens[0][1][0]
        query_end_pos = tokens[0][1][1]

        # Determine the search field of the search term.
        if len(tokens) > 1 and self.is_search_field(tokens[1][0]):
            search_field = SearchField(value=tokens[1][0], position=tokens[1][1])
            query_end_pos = tokens[1][1][1]
        else:
            # Select default field "all" if no search field is found.
            search_field = SearchField(value=Fields.ALL)

        return Query(
            value=search_term[0],
            operator=False,
            search_field=search_field,
            position=(query_start_pos, query_end_pos),
        )

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields"""

        if query.children:
            for query in query.children:
                self.translate_search_fields(query)
            return

        query.search_field.value = self._map_default_field(query.search_field.value)

        # Convert queries in the form 'Term [tiab]' into 'Term [ti] OR Term [ab]'.
        if query.search_field.value == "[tiab]":
            self._expand_combined_fields(query, [Fields.TITLE, Fields.ABSTRACT])
            return

        # Translate search fields to standard field constants.
        if query.search_field.value in self.FIELD_TRANSLATION_MAP:
            query.search_field.value = self.FIELD_TRANSLATION_MAP[
                query.search_field.value
            ]

    def parse_user_provided_fields(self, field_values: str) -> list:
        """Extract and translate user-provided search fields and return them as a list"""
        if not field_values:
            return []

        field_values = [
            search_field.strip() for search_field in field_values.split(",")
        ]

        for index, value in enumerate(field_values):
            value = "[" + value.lower() + "]"

            value = self._map_default_field(value)

            if value in {"[title and abstract]", "[tiab]"}:
                value = Fields.TITLE
                field_values.insert(index + 1, Fields.ABSTRACT)

            if value in {"[subject headings]"}:
                value = Fields.MESH_TERM

            if value in self.FIELD_TRANSLATION_MAP:
                value = self.FIELD_TRANSLATION_MAP[value]

            field_values[index] = value

        return field_values

    def _map_default_field(self, field_value) -> str:
        """Convert search fields to their abbreviated forms (e.g. "[title] -> "[ti]")"""
        if field_value.lower() in self.DEFAULT_FIELD_MAP:
            return self.DEFAULT_FIELD_MAP.get(field_value.lower())
        else:
            return field_value.lower()

    def _expand_combined_fields(self, query: Query, search_fields: list) -> None:
        """Expand queries with combined search fields into an OR query"""
        query_children = []

        for search_field in search_fields:
            query_children.append(
                Query(
                    value=query.value,
                    operator=False,
                    search_field=SearchField(value=search_field),
                    children=None,
                )
            )

        query.value = Operators.OR
        query.operator = True
        query.search_field.value = Fields.ALL
        query.children = query_children

    def _get_query_leaves(self, query: Query) -> list:
        """Retrieve all leaf nodes from a query, representing search terms and fields, and return them as a list"""
        if not query.children:
            return [query]

        leaves = []
        for child in query.children:
            leaves += self._get_query_leaves(child)
        return leaves

    def parse(self) -> Query:
        """Parse a query string"""
        self.linter_messages = []

        # Tokenization
        self.tokenize()
        refined_tokens = self.validate_tokens(self.tokens.copy())
        self.check_linter_status()

        # Parsing
        query = self.parse_query_tree(refined_tokens)
        self.validate_query_tree(query)
        self.check_linter_status()

        # Search field mapping
        self.translate_search_fields(query)
        user_field_values = self.parse_user_provided_fields(self.search_fields)
        self.validate_search_fields(query, user_field_values)
        self.check_linter_status()

        return query

    """Linter methods below this point"""

    def validate_tokens(self, tokens: list) -> list:
        """Validate token list"""
        invalid_token_indices = []

        self._check_unbalanced_parentheses(tokens, invalid_token_indices)

        for index, token in enumerate(tokens):
            if self.is_term(token[0]):
                self._check_invalid_characters(index, tokens, invalid_token_indices)
                if "*" in token[0]:
                    self._check_invalid_wildcard(index, tokens)
            else:
                self._check_invalid_token_position(index, tokens, invalid_token_indices)

            if (
                index not in invalid_token_indices
                and self.is_search_field(token[0])
                and ":~" in token[0]
            ):
                self._check_invalid_proximity_operator(index, tokens)

            if (
                index > 0
                and index not in invalid_token_indices
                and index - 1 not in invalid_token_indices
            ):
                self._check_missing_operator(index, tokens)

        [val for i, val in enumerate(tokens) if i not in invalid_token_indices]
        self._check_precedence(tokens)

        return tokens

    def _check_unbalanced_parentheses(
        self, tokens: list, invalid_token_indices: list
    ) -> None:
        """Check token list for unbalanced parentheses"""
        i = 0
        for index, token in enumerate(tokens):
            if token[0] == "(":
                i += 1
            elif token[0] == ")":
                if i == 0:
                    # Query contains unbalanced closing parentheses
                    self.add_linter_message(
                        PubmedErrorCodes.UNBALANCED_PARENTHESES, token[1]
                    )
                    invalid_token_indices.append(index)
                else:
                    i -= 1

        if i > 0:
            # Query contains unbalanced opening parentheses
            last_index = len(tokens) - 1
            for index, token in enumerate(reversed(tokens)):
                if token[0] == "(":
                    self.add_linter_message(
                        PubmedErrorCodes.UNBALANCED_PARENTHESES, token[1]
                    )
                    invalid_token_indices.append(last_index - index)
                    i -= 1
                if i == 0:
                    break

    def _check_precedence(self, tokens: list) -> None:
        """Check token list contain unspecified precedence (OR & AND operator in the same subquery)"""
        or_query = False
        for token in tokens:
            if token[0] == Operators.OR:
                or_query = True
            elif self.is_parenthesis(token[0]):
                or_query = False
            elif token[0] == Operators.AND and or_query:
                self.add_linter_message(PubmedErrorCodes.PRECEDENCE_WARNING, token[1])

    def _check_invalid_characters(
        self, index: int, tokens: list, invalid_token_indices: list
    ) -> None:
        """Check a search term for invalid characters"""

        invalid_characters = "!#$%+.;<>?\\^_{}~'()"

        token = tokens[index]
        term_value = token[0]
        # Iterate over term to identify invalid characters and replace them with whitespace
        for i, char in enumerate(token[0]):
            if char in invalid_characters:
                self.add_linter_message(
                    PubmedErrorCodes.INVALID_CHARACTER, token[1], char
                )
                term_value = term_value[:i] + " " + term_value[i + 1 :]
            elif char in "[]":
                self.add_linter_message(
                    PubmedErrorCodes.INVALID_BRACKET_USE,
                    (token[1][0] + i, token[1][0] + i + 1),
                )
        # Update token
        if term_value != token[0]:
            tokens[index] = (term_value, token[1])
            if term_value.isspace():
                invalid_token_indices.append(index)

    def _check_invalid_wildcard(self, index: int, tokens: list):
        """Check search term for invalid wildcard *"""
        token = tokens[index]
        if token[0][0] == '"':
            k = 5
        else:
            k = 4
        if "*" in token[0][:k]:
            # Wildcard * is invalid if it is applied to terms with less than 4 characters
            self.add_linter_message(PubmedErrorCodes.INVALID_WILDCARD, token[1])

    def _check_invalid_token_position(
        self, index: int, tokens: list, invalid_token_indices: list
    ):
        """Check if tokens contains invalid token position at index"""
        if index == 0:
            prev_token = None
        else:
            prev_token = tokens[index - 1]

        if index == len(tokens) - 1:
            next_token = None
        else:
            next_token = tokens[index + 1]

        current_token = tokens[index]

        if self.is_operator(current_token[0]):
            if not (
                prev_token
                and (
                    self.is_term(prev_token[0])
                    or self.is_search_field(prev_token[0])
                    or prev_token[0] == ")"
                )
            ):
                # Invalid operator position
                self.add_linter_message(
                    PubmedErrorCodes.INVALID_OPERATOR_POSITION, current_token[1]
                )
                invalid_token_indices.append(index)
            elif not (
                next_token and (self.is_term(next_token[0]) or next_token[0] == "(")
            ):
                # Invalid operator position
                self.add_linter_message(
                    PubmedErrorCodes.INVALID_OPERATOR_POSITION, current_token[1]
                )
                invalid_token_indices.append(index)

        elif self.is_search_field(current_token[0]):
            if not (prev_token and self.is_term(prev_token[0])):
                # Invalid search field position
                self.add_linter_message(
                    PubmedErrorCodes.INVALID_FIELD_POSITION, current_token[1]
                )
                invalid_token_indices.append(index)

        elif current_token[0] == "(":
            if next_token and next_token[0] == ")":
                # Empty parentheses
                self.add_linter_message(
                    PubmedErrorCodes.EMPTY_PARENTHESES,
                    (current_token[1][0], next_token[1][1]),
                )

    def _check_invalid_proximity_operator(self, index: int, tokens: list) -> None:
        """Check search field for invalid proximity operator"""
        search_field_token = tokens[index]
        search_phrase_token = tokens[index - 1]

        match = re.match(self.PROXIMITY_REGEX, search_field_token[0])
        if match:
            search_field_value, prox_value = match.groups()
            if not prox_value.isdigit():
                prox_value_pos = tuple(
                    pos + search_phrase_token[1][0] for pos in match.span(2)
                )
                self.add_linter_message(
                    PubmedErrorCodes.INVALID_PROXIMITY_DISTANCE, prox_value_pos
                )
            else:
                nr_of_terms = len(search_phrase_token[0].strip('"').split())
                if not (
                    search_phrase_token[0][0] == '"'
                    and search_phrase_token[0][-1] == '"'
                    and nr_of_terms >= 2
                ):
                    self.add_linter_message(
                        PubmedErrorCodes.INVALID_PROXIMITY_USE,
                        search_phrase_token[1],
                        "Proximity search should be applied to quoted search phrases with at least two terms.",
                    )

                search_field_value = self._map_default_field(search_field_value.lower())
                if search_field_value not in {"tiab", "ti", "ad"}:
                    self.add_linter_message(
                        PubmedErrorCodes.INVALID_PROXIMITY_USE,
                        search_phrase_token[1],
                        "Proximity search is only supported for Title, Title/Abstract and Affiliation fields.",
                    )

            # Update search field token
            tokens[index] = ("[" + search_field_value + "]", search_field_token[1])
        else:
            self.add_linter_message(
                PubmedErrorCodes.INVALID_PROXIMITY_SYNTAX, search_phrase_token[1]
            )

    def _check_missing_operator(self, index: int, tokens: list) -> None:
        """Check if there is a missing operator between previous and current token"""
        token_1 = tokens[index - 1]
        token_2 = tokens[index]
        if (
            token_1[0] == ")"
            or self.is_term(token_1[0])
            or self.is_search_field(token_1[0])
        ) and (token_2[0] == "(" or self.is_term(token_2[0])):
            self.add_linter_message(
                PubmedErrorCodes.MISSING_OPERATOR, (token_1[1][0], token_2[1][1])
            )

    def validate_query_tree(self, query: Query) -> None:
        """Validate the query tree"""
        self._check_nested_not_query(query)
        self._check_redundant_terms(query)

    def _check_nested_not_query(self, query: Query) -> None:
        """Check query tree for nested NOT queries"""
        for child in query.children:
            if child.operator and child.value == Operators.NOT:
                self.add_linter_message(
                    PubmedErrorCodes.NESTED_NOT_QUERY, child.position
                )
            self._check_nested_not_query(child)

    def _check_redundant_terms(self, query: Query) -> None:
        """Check query for redundant search terms"""
        subqueries = {}
        subquery_types = {}
        self._extract_subqueries(query, subqueries, subquery_types)

        # Compare search terms in the same subquery for redundancy
        for query_id in subqueries.keys():
            terms = subqueries[query_id]

            # Exclude subqueries without search terms
            if not terms:
                continue

            redundant_terms = []

            if query_id not in subquery_types:
                continue

            operator = subquery_types[query_id]

            if operator == Operators.NOT:
                terms.pop(0)  # First term of a NOT query cannot be redundant

            for k in range(len(terms)):
                for i in range(len(terms)):
                    if (
                        k == i
                        or terms[k] in redundant_terms
                        or terms[i] in redundant_terms
                    ):
                        continue

                    field_value_1 = self._map_default_field(
                        terms[k].search_field.value.lower()
                    )
                    field_value_2 = self._map_default_field(
                        terms[i].search_field.value.lower()
                    )

                    if field_value_1 == field_value_2 and (
                        terms[k].value == terms[i].value
                        or (
                            field_value_1 != "[mh]"
                            and terms[k].value.strip('"').lower()
                            in terms[i].value.strip('"').lower().split()
                        )
                    ):
                        # Terms in AND queries follow different redundancy logic than terms in OR queries
                        if operator == Operators.AND:
                            self.add_linter_message(
                                PubmedErrorCodes.TERM_REDUNDANT, terms[k].position
                            )
                            redundant_terms.append(terms[k])
                        elif operator in {Operators.OR, Operators.NOT}:
                            self.add_linter_message(
                                PubmedErrorCodes.TERM_REDUNDANT, terms[i].position
                            )
                            redundant_terms.append(terms[i])

    def _extract_subqueries(
        self, query: Query, subqueries: dict, subquery_types: dict, subquery_id=0
    ) -> None:
        """Extract subqueries from query tree"""
        if subquery_id not in subqueries:
            subqueries[subquery_id] = []
            if query.operator:
                subquery_types[subquery_id] = query.value

        for child in query.children:
            if not child.children:
                subqueries.get(subquery_id).append(child)
            elif child.value == query.value:
                self._extract_subqueries(child, subqueries, subquery_types, subquery_id)
            else:
                new_subquery_id = max(subqueries.keys()) + 1
                self._extract_subqueries(
                    child, subqueries, subquery_types, new_subquery_id
                )

        if not query.children:
            subqueries.get(subquery_id).append(query)

    def validate_search_fields(self, query: Query, user_field_values: list) -> None:
        """Validate search terms and fields"""
        leaf_queries = self._get_query_leaves(query)

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
            self.add_linter_message(
                PubmedErrorCodes.UNSUPPORTED_FIELD, search_field.position
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
                    PubmedErrorCodes.FIELD_CONTRADICTION, None, self.search_fields
                )
            else:
                # User-provided fields match fields in the query
                self.add_linter_message(PubmedErrorCodes.FIELD_REDUNDANT, None)

        elif user_field_values and not query_field_values:
            # User-provided fields are missing in the query
            self.add_linter_message(
                PubmedErrorCodes.MISSING_QUERY_FIELD, None, self.search_fields
            )

        elif not user_field_values and not query_field_values:
            # Fields not specified
            self.add_linter_message(PubmedErrorCodes.FIELD_NOT_SPECIFIED, None)

    def add_linter_message(
        self, code: str, position: typing.Optional[tuple], error_details: str = None
    ) -> None:
        """Add a linter message"""

        message = self.DEFAULT_ERROR_MESSAGES.get(code)

        if error_details:
            message += " " + error_details

        if self.mode != "strict" and code in self.NON_STRICT_CORRECTION_MESSAGES:
            message += "\n" + self.NON_STRICT_CORRECTION_MESSAGES.get(code)

        self.linter_messages.append(
            {"code": code, "message": message, "position": position}
        )

    def check_linter_status(self) -> None:
        """Check the output of the linter and report errors to the user"""
        while self.linter_messages:
            msg = self.linter_messages.pop(0)
            e = self._get_exception(msg)

            code = msg.get("code")
            # Always raise an exception for fatal messages
            if code[0] == "F":
                raise e

            # Raise an exception for error messages if in strict mode
            elif code[0] == "E":
                if self.mode == "strict":
                    raise e
                else:
                    print(e)

            elif code[0] == "W":
                if not self.silence_warnings:
                    print(e)

            print("\n")

    def _get_exception(self, msg: dict) -> SearchQueryException:
        """Retrieve the corresponding exception for a linter message"""
        code = msg.get("code")
        user_message = str(msg.get("message"))
        pos = msg.get("position")

        exception_map = {
            # Syntax Errors
            PubmedErrorCodes.UNBALANCED_PARENTHESES: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.MISSING_OPERATOR: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.INVALID_BRACKET_USE: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.INVALID_OPERATOR_POSITION: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.INVALID_FIELD_POSITION: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.EMPTY_PARENTHESES: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.INVALID_PROXIMITY_DISTANCE: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.INVALID_PROXIMITY_USE: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.INVALID_PROXIMITY_SYNTAX: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.INVALID_CHARACTER: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.INVALID_WILDCARD: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.NESTED_NOT_QUERY: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            # Invalid Field Error
            PubmedErrorCodes.UNSUPPORTED_FIELD: lambda: PubmedInvalidFieldTag(
                user_message, self.query_str, pos
            ),
            # Field Mismatch Error
            PubmedErrorCodes.MISSING_QUERY_FIELD: lambda: PubmedFieldMismatch(
                user_message
            ),
            PubmedErrorCodes.FIELD_CONTRADICTION: lambda: PubmedFieldMismatch(
                user_message
            ),
            # Warnings
            PubmedErrorCodes.FIELD_REDUNDANT: lambda: PubmedFieldWarning(user_message),
            PubmedErrorCodes.FIELD_NOT_SPECIFIED: lambda: PubmedFieldWarning(
                user_message
            ),
            PubmedErrorCodes.TERM_REDUNDANT: lambda: PubmedQueryWarning(
                user_message, self.query_str, pos
            ),
            PubmedErrorCodes.PRECEDENCE_WARNING: lambda: PubmedQueryWarning(
                user_message, self.query_str, pos
            ),
        }
        return exception_map.get(code)()


class PubmedListParser(QueryListParser):
    """Parser for Pubmed (list format) queries."""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"

    def __init__(self, query_list: str) -> None:
        super().__init__(query_list, PubmedParser)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

    def parse(self) -> Query:
        """Parse the query in list format."""

        tokens = self.parse_dict()

        query_list = self.dict_to_positioned_list(tokens)
        query_string = "".join([query[0] for query in query_list])

        try:
            query = self.parser_class(query_string).parse()

        except (QuerySyntaxError, PubmedInvalidFieldTag, PubmedQueryWarning) as exc:
            # Correct positions and query string
            # to display the error for the original (list) query
            new_pos = exc.pos
            for content, pos in query_list:
                # Note: artificial parentheses cannot be ignored here
                # because they were counted in the query_string
                segment_length = len(content)

                if new_pos[0] - segment_length >= 0:
                    new_pos = (new_pos[0] - segment_length, new_pos[1] - segment_length)
                    continue
                segment_beginning = pos[0]
                new_pos = (
                    new_pos[0] + segment_beginning,
                    new_pos[1] + segment_beginning,
                )
                exc.pos = new_pos
                break

            exc.query_string = self.query_list

            exception_type = type(exc)
            raise exception_type(
                msg=exc.message.split("\n")[0],
                query_string=exc.query_string,
                pos=exc.pos,
            ) from None

        return query
