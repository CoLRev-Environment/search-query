#!/usr/bin/env python3
"""Pubmed query parser."""
import re

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
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

    SEARCH_FIELD_REGEX = r"\[[^\[]*?\]"
    OPERATOR_REGEX = r"(\||&|\b(?:AND|OR|NOT)\b)(?!\s?\[[^\[]*?\])"
    PARENTHESIS_REGEX = r"[\(\)]"
    SEARCH_PHRASE_REGEX = r"\".*?\""
    SEARCH_TERM_REGEX = r"[^\s\[\]()]+"
    PROXIMITY_REGEX = r"^\[(.+):~(.*)\]$"

    pattern = "|".join(
        [
            SEARCH_FIELD_REGEX,
            OPERATOR_REGEX,
            PARENTHESIS_REGEX,
            SEARCH_PHRASE_REGEX,
            SEARCH_TERM_REGEX,
        ]
    )

    def tokenize(self) -> None:
        """Tokenize the query_str"""
        # Parse tokens and positions based on regex patterns.
        prev_end = 0
        for match in re.finditer(self.pattern, self.query_str, re.IGNORECASE):
            value = match.group(0)
            start, end = match.span()

            if start > prev_end and self.query_str[prev_end:start].strip():
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED, (prev_end, start)
                )

            if value.upper() in {"AND", "OR", "NOT", "|", "&"}:
                token_type = TokenTypes.LOGIC_OPERATOR
            elif value == "(":
                token_type = TokenTypes.PARENTHESIS_OPEN
            elif value == ")":
                token_type = TokenTypes.PARENTHESIS_CLOSED
            elif value.startswith("[") and value.endswith("]"):
                token_type = TokenTypes.FIELD
            else:
                token_type = TokenTypes.SEARCH_TERM

            prev_end = end
            self.tokens.append(
                Token(value=value, type=token_type, position=(start, end))
            )

        if prev_end < len(self.query_str) and self.query_str[:prev_end].strip():
            self.add_linter_message(
                QueryErrorCode.TOKENIZING_FAILED, (prev_end, len(self.query_str))
            )

        self.combine_subsequent_terms()

    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return bool(re.match(r"^\[.*]$", token))

    def get_operator_type(self, operator: str) -> str:
        """Get operator type"""
        if operator.upper() in {"&", "AND"}:
            return Operators.AND
        elif operator.upper() in {"|", "OR"}:
            return Operators.OR
        elif operator.upper() == "NOT":
            return Operators.NOT
        else:
            raise ValueError()

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
        return tokens[0].type == TokenTypes.SEARCH_TERM and len(tokens) <= 2

    def is_compound_query(self, tokens):
        return bool(self._get_operator_indices(tokens))

    def is_nested_query(self, tokens):
        return (
            tokens[0].type == TokenTypes.PARENTHESIS_OPEN
            and tokens[-1].type == TokenTypes.PARENTHESIS_CLOSED
        )

    def _get_operator_indices(self, tokens: list) -> list:
        """Get indices of top-level operators in the token list"""
        operator_indices = []

        i = 0
        first_operator_found = False
        first_operator = ""
        # Iterate over tokens in reverse to find and save positions of consecutive top-level operators
        # matching the first encountered until a different type is found.
        for token in reversed(tokens):
            token_index = tokens.index(token)

            if token.type == TokenTypes.PARENTHESIS_OPEN:
                i = i + 1
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                i = i - 1

            if i == 0 and token.type == TokenTypes.LOGIC_OPERATOR:
                operator = self.get_operator_type(token.value)
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

        operator_type = self.get_operator_type(tokens[operator_indices[0]].value)

        query_start_pos = tokens[0].position[0]
        query_end_pos = tokens[-1].position[1]

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
        search_term_token = tokens[0]
        query_end_pos = tokens[0].position[1]

        # Determine the search field of the search term.
        if len(tokens) > 1 and tokens[1].type == TokenTypes.FIELD:
            search_field = SearchField(
                value=tokens[1].value, position=tokens[1].position
            )
            query_end_pos = tokens[1].position[1]
        else:
            # Select default field "all" if no search field is found.
            search_field = SearchField(value=Fields.ALL)

        return Query(
            value=search_term_token.value,
            operator=False,
            search_field=search_field,
            position=(tokens[0].position[0], query_end_pos),
        )

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields"""

        if query.children:
            for query in query.children:
                self.translate_search_fields(query)
            return

        query.search_field.value = self._map_search_field(query.search_field.value)

        # Convert queries in the form 'Term [tiab]' into 'Term [ti] OR Term [ab]'.
        if query.search_field.value == "[tiab]":
            self._expand_combined_fields(query, [Fields.TITLE, Fields.ABSTRACT])
            return

    def parse_user_provided_fields(self, field_values: str) -> list:
        """Extract and translate user-provided search fields and return them as a list"""
        if not field_values:
            return []

        field_values = [
            search_field.strip() for search_field in field_values.split(",")
        ]

        for index, value in enumerate(field_values):
            value = "[" + value.lower() + "]"

            value = self._map_search_field(value)

            if value in {"[title and abstract]", "[tiab]"}:
                value = Fields.TITLE
                field_values.insert(index + 1, Fields.ABSTRACT)

            if value in {"[subject headings]"}:
                value = Fields.MESH_TERM

            field_values[index] = value

        return field_values

    def _map_search_field(self, field_value) -> str:
        """Translate a search field"""
        field_value = field_value.lower()
        # Convert search fields to their abbreviated forms (e.g. "[title] -> "[ti]")
        if field_value in self.DEFAULT_FIELD_MAP:
            field_value = self.DEFAULT_FIELD_MAP.get(field_value)
        # Convert search fields to default field constants
        if field_value in self.FIELD_TRANSLATION_MAP:
            field_value = self.FIELD_TRANSLATION_MAP.get(field_value)
        return field_value

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
                    self.add_linter_message(
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
                    self.add_linter_message(
                        QueryErrorCode.UNBALANCED_PARENTHESES, token.position
                    )
                    invalid_token_indices.append(last_index - index)
                    i -= 1
                if i == 0:
                    break

    def _check_precedence(self, tokens: list) -> None:
        """Check token list contain unspecified precedence (OR & AND operator in the same subquery)"""
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
                self.add_linter_message(QueryErrorCode.QUERY_PRECEDENCE, token.position)

    def _check_invalid_characters(
        self, index: int, tokens: list, invalid_token_indices: list
    ) -> None:
        """Check a search term for invalid characters"""

        invalid_characters = "!#$%+.;<>?\\^_{}~'()[]"

        token = tokens[index]
        value = token.value
        # Iterate over term to identify invalid characters and replace them with whitespace
        for i, char in enumerate(token.value):
            if char in invalid_characters:
                self.add_linter_message(
                    QueryErrorCode.INVALID_CHARACTER, token.position
                )
                value = value[:i] + " " + value[i + 1 :]
        # Update token
        if value != token.value:
            token.value = value
            if value.isspace():
                invalid_token_indices.append(index)

    def _check_invalid_wildcard(self, index: int, tokens: list):
        """Check search term for invalid wildcard *"""
        token = tokens[index]
        if token.value == '"':
            k = 5
        else:
            k = 4
        if "*" in token.value[:k]:
            # Wildcard * is invalid if it is applied to terms with less than 4 characters
            self.add_linter_message(QueryErrorCode.INVALID_WILDCARD_USE, token.position)

    def _check_invalid_token_position(
        self, index: int, tokens: list, invalid_token_indices: list
    ):
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
                self.add_linter_message(
                    QueryErrorCode.EMPTY_PARENTHESES,
                    (current_token.position[0], next_token.position[1]),
                )
                invalid_token_indices.append(index)
                invalid_token_indices.append(index + 1)

        if current_token.type == TokenTypes.LOGIC_OPERATOR:
            if not (
                prev_token
                and (
                    prev_token.type == TokenTypes.SEARCH_TERM
                    or prev_token.type == TokenTypes.FIELD
                    or prev_token.type == TokenTypes.PARENTHESIS_CLOSED
                )
            ):
                # Invalid operator position
                self.add_linter_message(
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
                self.add_linter_message(
                    QueryErrorCode.INVALID_OPERATOR_POSITION, current_token.position
                )
                invalid_token_indices.append(index)

        elif current_token.type == TokenTypes.FIELD:
            if not (prev_token and prev_token.type == TokenTypes.SEARCH_TERM):
                # Invalid search field position
                self.add_linter_message(
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
                self.add_linter_message(
                    QueryErrorCode.INVALID_PROXIMITY_USE, field_token.position
                )
            else:
                nr_of_terms = len(search_phrase_token.value.strip('"').split())
                if not (
                    search_phrase_token.value[0] == '"'
                    and search_phrase_token.value[-1] == '"'
                    and nr_of_terms >= 2
                ):
                    self.add_linter_message(
                        QueryErrorCode.INVALID_PROXIMITY_USE, field_token.position
                    )

                if self._map_search_field(field_value) not in {"tiab", Fields.TITLE, Fields.AFFILIATION}:
                    self.add_linter_message(
                        QueryErrorCode.INVALID_PROXIMITY_USE, field_token.position
                    )

            # Update search field token
            tokens[index].value = field_value
        else:
            self.add_linter_message(
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
            self.add_linter_message(
                QueryErrorCode.MISSING_OPERATOR,
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
                self.add_linter_message(QueryErrorCode.NESTED_NOT_QUERY, child.position)
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

                    field_value_1 = self._map_search_field(
                        terms[k].search_field.value
                    )
                    field_value_2 = self._map_search_field(
                        terms[i].search_field.value
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
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                terms[k].position,
                            )
                            redundant_terms.append(terms[k])
                        elif operator in {Operators.OR, Operators.NOT}:
                            self.add_linter_message(
                                QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
                                terms[i].position,
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
                self.add_linter_message(QueryErrorCode.SEARCH_FIELD_CONTRADICTION, None)
            else:
                # User-provided fields match fields in the query
                self.add_linter_message(QueryErrorCode.SEARCH_FIELD_REDUNDANT, None)

        elif user_field_values and not query_field_values:
            # User-provided fields are missing in the query
            self.add_linter_message(QueryErrorCode.SEARCH_FIELD_MISSING, None)

        elif not user_field_values and not query_field_values:
            # Fields not specified
            self.add_linter_message(QueryErrorCode.SEARCH_FIELD_NOT_SPECIFIED, None)

    def check_linter_status(self) -> None:
        """Check the output of the linter and report errors to the user"""
        while self.linter_messages:
            msg = self.linter_messages.pop(0)
            e = self._get_exception(msg)

            code = msg.get("code")
            # Always raise an exception for fatal messages
            if code.startswith("F"):
                raise e

            # Raise an exception for error messages if in strict mode
            elif code.startswith("E"):
                if self.mode == "strict":
                    raise e
                else:
                    print(e)

            elif code.startswith("W"):
                if not self.silence_warnings:
                    print(e)

            print("\n")

    def _get_exception(self, msg: dict) -> SearchQueryException:
        """Retrieve the corresponding exception for a linter message"""
        code = msg.get("code")
        user_message = str(msg.get("message"))
        pos = msg.get("pos")

        exception_map = {
            # Syntax Errors
            QueryErrorCode.TOKENIZING_FAILED.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.UNBALANCED_PARENTHESES.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.MISSING_OPERATOR.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.INVALID_OPERATOR_POSITION.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.INVALID_SEARCH_FIELD_POSITION.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.INVALID_PROXIMITY_USE.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.INVALID_CHARACTER.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.INVALID_WILDCARD_USE.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.NESTED_NOT_QUERY.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.EMPTY_PARENTHESES.code: lambda: QuerySyntaxError(
                user_message, self.query_str, pos
            ),
            # Invalid Field Error
            QueryErrorCode.SEARCH_FIELD_UNSUPPORTED.code: lambda: PubmedInvalidFieldTag(
                user_message, self.query_str, pos
            ),
            # Field Mismatch Error
            QueryErrorCode.SEARCH_FIELD_MISSING.code: lambda: PubmedFieldMismatch(
                user_message
            ),
            QueryErrorCode.SEARCH_FIELD_CONTRADICTION.code: lambda: PubmedFieldMismatch(
                user_message
            ),
            # Warnings
            QueryErrorCode.SEARCH_FIELD_REDUNDANT.code: lambda: PubmedFieldWarning(
                user_message
            ),
            QueryErrorCode.SEARCH_FIELD_NOT_SPECIFIED.code: lambda: PubmedFieldWarning(
                user_message
            ),
            QueryErrorCode.QUERY_STRUCTURE_COMPLEX.code: lambda: PubmedQueryWarning(
                user_message, self.query_str, pos
            ),
            QueryErrorCode.QUERY_PRECEDENCE.code: lambda: PubmedQueryWarning(
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
