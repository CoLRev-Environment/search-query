#!/usr/bin/env python3
"""Pubmed query parser."""
import re

from search_query.constants import Fields
from search_query.constants import LinterMode
from search_query.constants import ListToken
from search_query.constants import ListTokenTypes
from search_query.constants import OperatorNodeTokenTypes
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import QuerySyntaxError
from search_query.linter_pubmed import PubmedQueryListLinter
from search_query.linter_pubmed import PubmedQueryStringLinter
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.query import Term


class PubmedParser(QueryStringParser):
    """Parser for Pubmed queries."""

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
        "[pdate]": "[dp]",
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
    SEARCH_TERM_REGEX = r"[^\s\[\]()\|&]+"
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

    def __init__(
        self,
        query_str: str,
        search_field_general: str = "",
        mode: str = LinterMode.NONSTRICT,
    ) -> None:
        """Initialize the parser."""
        super().__init__(
            query_str=query_str, search_field_general=search_field_general, mode=mode
        )
        self.linter = PubmedQueryStringLinter(self)

    def tokenize(self) -> None:
        """Tokenize the query_str"""
        if self.query_str is None:
            raise ValueError("No string provided to parse.")

        # Parse tokens and positions based on regex patterns.
        prev_end = 0
        for match in re.finditer(self.pattern, self.query_str, re.IGNORECASE):
            value = match.group(0)
            start, end = match.span()

            if start > prev_end and self.query_str[prev_end:start].strip():
                self.linter.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED, position=(prev_end, start)
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
            self.linter.add_linter_message(
                QueryErrorCode.TOKENIZING_FAILED,
                position=(prev_end, len(self.query_str)),
            )

        self.combine_subsequent_terms()

    def get_operator_type(self, operator: str) -> str:
        """Get operator type"""
        if operator.upper() in {"&", "AND"}:
            return Operators.AND
        if operator.upper() in {"|", "OR"}:
            return Operators.OR
        if operator.upper() == "NOT":
            return Operators.NOT
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

    def is_term_query(self, tokens: list) -> bool:
        """Check if the query is a search term"""
        return tokens[0].type == TokenTypes.SEARCH_TERM and len(tokens) <= 2

    def is_compound_query(self, tokens: list) -> bool:
        """Check if the query is a compound query"""
        return bool(self._get_operator_indices(tokens))

    def is_nested_query(self, tokens: list) -> bool:
        """Check if the query is nested in parentheses"""
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
        # Iterate over tokens in reverse
        # to find and save positions of consecutive top-level operators
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
        """Parse a compound query
        consisting of two or more subqueries connected by a boolean operator"""

        operator_indices = self._get_operator_indices(tokens)

        # Divide tokens into separate lists based on top-level operator positions.
        token_lists = []
        i = 0
        for position in reversed(operator_indices):
            token_lists.append(tokens[i:position])
            i = position + 1
        token_lists.append(tokens[i:])

        # The token lists represent the subqueries (children
        # of the compound query and are parsed individually.
        children = []
        for token_list in token_lists:
            query = self.parse_query_tree(token_list)
            children.append(query)

        operator_type = self.get_operator_type(tokens[operator_indices[0]].value)

        query_start_pos = tokens[0].position[0]
        query_end_pos = tokens[-1].position[1]

        return Query(
            value=operator_type,
            search_field=None,
            children=list(children),
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

        return Term(
            value=search_term_token.value,
            search_field=search_field,
            position=(tokens[0].position[0], query_end_pos),
        )

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields"""

        if query.children:
            for child in query.children:
                self.translate_search_fields(child)
            return

        if query.search_field:
            query.search_field.value = self.map_search_field(query.search_field.value)

            # Convert queries in the form 'Term [tiab]' into 'Term [ti] OR Term [ab]'.
            if query.search_field.value == "[tiab]":
                self._expand_combined_fields(query, [Fields.TITLE, Fields.ABSTRACT])

    def parse_user_provided_fields(self, field_values: str) -> list:
        """Extract and translate user-provided search fields (return as a list)"""
        if not field_values:
            return []

        field_values_list = [
            search_field.strip() for search_field in field_values.split(",")
        ]

        for index, value in enumerate(field_values_list):
            value = "[" + value.lower() + "]"

            value = self.map_search_field(value)

            if value in {"[title and abstract]", "[tiab]"}:
                value = Fields.TITLE
                field_values_list.insert(index + 1, Fields.ABSTRACT)

            if value in {"[subject headings]"}:
                value = Fields.MESH_TERM

            field_values_list[index] = value

        return field_values_list

    def map_search_field(self, field_value: str) -> str:
        """Translate a search field"""
        field_value = field_value.lower()
        # Convert search fields to their abbreviated forms (e.g. "[title] -> "[ti]")
        if field_value in self.DEFAULT_FIELD_MAP:
            field_value = self.DEFAULT_FIELD_MAP[field_value]
        # Convert search fields to default field constants
        if field_value in self.FIELD_TRANSLATION_MAP:
            field_value = self.FIELD_TRANSLATION_MAP[field_value]
        return field_value

    def _expand_combined_fields(self, query: Query, search_fields: list) -> None:
        """Expand queries with combined search fields into an OR query"""
        query_children = []

        for search_field in search_fields:
            query_children.append(
                Term(
                    value=query.value,
                    search_field=SearchField(value=search_field),
                    children=None,
                )
            )

        query.value = Operators.OR
        query.operator = True
        query.search_field = None
        query.children = query_children  # type: ignore

    def get_query_leaves(self, query: Query) -> list:
        """Retrieve all leaf nodes from a query,
        representing search terms and fields,
        and return them as a list"""
        if not query.children:
            return [query]

        leaves = []
        for child in query.children:
            leaves += self.get_query_leaves(child)
        return leaves

    def parse(self) -> Query:
        """Parse a query string"""

        self.tokenize()
        self.linter.validate_tokens()
        self.linter.check_status()

        # Parsing
        query = self.parse_query_tree(self.tokens)
        self.linter.validate_query_tree(query)
        self.linter.check_status()

        # self.linter.validate_search_fields(query)
        # self.linter.check_status()
        query.origin_syntax = PLATFORM.PUBMED.value

        return query


class PubmedListParser(QueryListParser):
    """Parser for Pubmed (list format) queries."""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"
    LIST_ITEM_REF = r"#\d+"
    OPERATOR_NODE_REGEX = r"#\d|AND|OR|NOT"

    def __init__(
        self,
        query_list: str,
        *,
        search_field_general: str = "",
        mode: str = LinterMode.NONSTRICT,
    ) -> None:
        super().__init__(
            query_list,
            parser_class=PubmedParser,
            search_field_general=search_field_general,
            mode=mode,
        )
        self.linter = PubmedQueryListLinter(self, PubmedParser)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

    def get_operator_node_tokens(self, token_nr: int) -> list:
        """Get operator node tokens"""
        node_content = self.query_dict[token_nr]["node_content"]
        operator_node_tokens = []
        for match in re.finditer(self.OPERATOR_NODE_REGEX, node_content):
            value = match.group(0)
            start, end = match.span()
            if value.upper() in {"AND", "OR", "NOT"}:
                token_type = OperatorNodeTokenTypes.LOGIC_OPERATOR
            elif re.match(self.LIST_ITEM_REF, value):
                token_type = OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
            else:
                token_type = OperatorNodeTokenTypes.UNKNOWN
            operator_node_tokens.append(
                ListToken(
                    value=value, type=token_type, level=token_nr, position=(start, end)
                )
            )
        return operator_node_tokens

    def parse_operator_node(self, token_nr: int) -> Query:
        """Parse an operator node."""

        operator_node_tokens = self.get_operator_node_tokens(token_nr)

        children_tokens = [
            t.value.replace("#", "")
            for t in operator_node_tokens
            if t.type == OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
        ]
        children = [self.query_dict[token_nr]["query"] for token_nr in children_tokens]
        operator = operator_node_tokens[1].value
        if operator.upper() in {"&", "AND"}:
            operator = Operators.AND
        if operator.upper() in {"|", "OR"}:
            operator = Operators.OR

        return Query(
            value=operator,
            search_field=None,
            children=children,
            position=(1, 1),
        )

    def parse(self) -> Query:
        """Parse the query in list format."""

        self.tokenize_list()
        self.linter.validate_tokens()
        self.linter.check_status()

        for token_nr, query_element in self.query_dict.items():
            print(f"*** Query list element: #{token_nr} *************************")
            if query_element["type"] == ListTokenTypes.QUERY_NODE:
                parser = self.parser_class(
                    query_element["node_content"],
                    search_field_general=self.search_field_general,
                )
                try:
                    query_element["query"] = parser.parse()
                except QuerySyntaxError:
                    pass

                self.linter.messages[token_nr] = parser.linter.messages

            if query_element["type"] == ListTokenTypes.OPERATOR_NODE:
                query_element["query"] = self.parse_operator_node(
                    token_nr
                    # query_element["node_content"]
                )

        query = list(self.query_dict.values())[-1]["query"]

        # TODO : linter.check_status()

        return query
