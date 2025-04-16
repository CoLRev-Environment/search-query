#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import re
import typing

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
from search_query.constants import WOSSearchFieldList
from search_query.exception import FatalLintingException
from search_query.linter_wos import QueryLinter
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class WOSParser(QueryStringParser):
    """Parser for Web-of-Science queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.WOS]

    SEARCH_TERM_REGEX = r'\*?[\w-]+(?:[\*\$\?][\w-]*)*|"[^"]+"'
    LOGIC_OPERATOR_REGEX = r"\b(AND|and|OR|or|NOT|not)\b"
    PROXIMITY_OPERATOR_REGEX = r"\b(NEAR/\d{1,2}|near/\d{1,2}|NEAR|near)\b"
    SEARCH_FIELD_REGEX = r"\b\w{2}=|\b\w{3}="
    PARENTHESIS_REGEX = r"[\(\)]"
    SEARCH_FIELDS_REGEX = r"\b(?!and\b)[a-zA-Z]+(?:\s(?!and\b)[a-zA-Z]+)*"
    YEAR_REGEX = r"^\d{4}(-\d{4})?$"
    ISSN_REGEX = r"^\d{4}-\d{3}[\dX]$"
    ISBN_REGEX = (
        r"^(?:\d{1,5}-\d{1,7}-\d{1,7}-[\dX]|\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1})$"
    )
    DOI_REGEX = r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$"

    OPERATOR_REGEX = "|".join([LOGIC_OPERATOR_REGEX, PROXIMITY_OPERATOR_REGEX])

    # Combine all regex patterns into a single pattern
    pattern = "|".join(
        [
            SEARCH_FIELD_REGEX,
            LOGIC_OPERATOR_REGEX,
            PROXIMITY_OPERATOR_REGEX,
            SEARCH_TERM_REGEX,
            PARENTHESIS_REGEX,
            # self.SEARCH_FIELDS_REGEX,
        ]
    )

    def __init__(
        self,
        query_str: str,
        search_field_general: str = "",
        mode: str = LinterMode.STRICT,
    ) -> None:
        """Initialize the parser."""
        super().__init__(
            query_str=query_str, search_field_general=search_field_general, mode=mode
        )
        self.query_linter = QueryLinter(parser=self)

    def _handle_fully_quoted_query_str(self) -> None:
        if (
            '"' == self.query_str[0]
            and '"' == self.query_str[-1]
            and "(" in self.query_str
        ):
            self.add_linter_message(
                QueryErrorCode.QUERY_IN_QUOTES,
                position=(-1, -1),
            )
            # remove quotes before tokenization
            self.query_str = self.query_str[1:-1]

        # if self.parser.tokens[0].value in [
        #     "Web of Science",
        #     "wos",
        #     "WoS",
        #     "WOS",
        #     "WOS:",
        #     "WoS:",
        #     "WOS=",
        #     "WoS=",
        # ]:
        #     self.parser.add_linter_message(
        #         QueryErrorCode.QUERY_STARTS_WITH_PLATFORM_IDENTIFIER,
        #         position=self.parser.tokens[0][1],
        #     )
        #     # non-fatal error: remove identifier from tokens

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        self._handle_fully_quoted_query_str()

        # Parse tokens and positions based on regex pattern
        compile_pattern = re.compile(pattern=self.pattern)

        for match in compile_pattern.finditer(self.query_str):
            value = match.group()
            position = match.span()

            # Determine token type
            if re.fullmatch(self.PARENTHESIS_REGEX, value):
                if value == "(":
                    token_type = TokenTypes.PARENTHESIS_OPEN
                else:
                    token_type = TokenTypes.PARENTHESIS_CLOSED
            elif re.fullmatch(self.LOGIC_OPERATOR_REGEX, value):
                token_type = TokenTypes.LOGIC_OPERATOR
            elif re.fullmatch(self.PROXIMITY_OPERATOR_REGEX, value):
                token_type = TokenTypes.PROXIMITY_OPERATOR
            elif re.fullmatch(self.SEARCH_FIELD_REGEX, value):
                token_type = TokenTypes.FIELD
            elif re.fullmatch(self.SEARCH_TERM_REGEX, value):
                token_type = TokenTypes.SEARCH_TERM
            else:
                token_type = TokenTypes.UNKNOWN

            self.tokens.append(Token(value=value, type=token_type, position=position))

        self.combine_subsequent_terms()

    # Implement and override methods of parent class (as needed)
    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return (
            bool(re.match(self.SEARCH_FIELD_REGEX, token))
            or token in WOSSearchFieldList.language_list
        )

    # Parse a query tree from tokens recursively
    # pylint: disable=too-many-branches
    def parse_query_tree(
        self,
        index: int = 0,
        search_field: typing.Optional[SearchField] = None,
        superior_search_field: typing.Optional[SearchField] = None,
        current_negation: bool = False,
    ) -> typing.Tuple[Query, int]:
        """Parse tokens starting at the given index,
        handling parentheses, operators, search fields and terms recursively."""
        children: typing.List[Query] = []
        current_operator = ""

        if current_negation:
            current_operator = "NOT"

        while index < len(self.tokens):
            token = self.tokens[index]

            # Handle nested expressions within parentheses
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                if self.tokens[index - 1].type == TokenTypes.FIELD:
                    superior_search_field = self.tokens[index - 1].value

                # Parse the expression inside the parentheses
                sub_query, index = self.parse_query_tree(
                    index=index + 1,
                    search_field=search_field,
                    superior_search_field=superior_search_field,
                    current_negation=current_negation,
                )

                # Add the parsed expression to the list of children
                children = self.append_children(
                    children=children,
                    sub_query=sub_query,
                    current_operator=current_operator,
                )
                current_negation = False

            # Handle closing parentheses
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                superior_search_field = None
                return (
                    self.handle_closing_parenthesis(
                        children=children,
                        current_operator=current_operator,
                    ),
                    index,
                )

            # Handle operators
            elif token.type == TokenTypes.LOGIC_OPERATOR:
                # Handle the operator
                # and update all changes within the handler
                (
                    current_operator,
                    current_negation,
                ) = self.handle_operator(
                    token=token,
                    current_operator=current_operator,
                    current_negation=current_negation,
                )

            # Handle search fields
            elif token.type == TokenTypes.FIELD or (
                token.value in WOSSearchFieldList.language_list
            ):
                search_field = SearchField(value=token.value, position=token.position)

            # Handle terms
            else:
                # Check if the token is a search field which has constraints
                # Check if the token is a year
                if re.findall(self.YEAR_REGEX, token.value) and search_field:
                    if search_field.value in WOSSearchFieldList.year_published_list:
                        children = self.handle_year_search(
                            token, children, current_operator
                        )
                        index += 1
                        continue

                # Set search field to superior search field
                # if no search field is given
                if not search_field and superior_search_field:
                    search_field = superior_search_field

                # Set search field to ALL if no search field is given
                if not search_field:
                    search_field = SearchField("All", position=None)

                # Check if the token is ISSN or ISBN
                if search_field.value in WOSSearchFieldList.issn_isbn_list:
                    self.query_linter.check_issn_isbn_format(token)

                # Check if the token is a doi
                if search_field.value in WOSSearchFieldList.doi_list:
                    self.query_linter.check_doi_format(token)

                # Add term nodes
                children = self.add_term_node(
                    index=index,
                    value=token.value,
                    operator=False,
                    search_field=search_field,
                    position=token.position,
                    children=children,
                    current_operator=current_operator,
                    current_negation=current_negation,
                )

                current_operator = ""
                search_field_for_check = search_field.value

                if not (
                    superior_search_field
                    and superior_search_field == search_field_for_check
                ):
                    search_field = None

            index += 1

        # Return options if there are no more tokens
        # Return the children if there is only one child
        if len(children) == 1:
            return children[0], index

        # Return the operator and children if there is an operator
        if current_operator:
            return (
                Query(
                    value=current_operator,
                    operator=True,
                    children=list(children),
                    search_field=search_field,
                ),
                index,
            )

        # Raise an error if the code gets here
        raise NotImplementedError("Error in parsing the query tree")

    def handle_closing_parenthesis(
        self,
        children: list,
        current_operator: str,
    ) -> Query:
        """Handle closing parentheses."""
        # Return the children if there is only one child
        if len(children) == 1:
            return children[0]

        # Return the operator and children if there is an operator
        if current_operator:
            return Query(
                value=current_operator,
                operator=True,
                children=children,
            )

        # Multiple children without operator are not allowed
        # This should already be caught in the token validation
        raise ValueError(
            "[ERROR] Multiple children without operator are not allowed."
            + "\nFound: "
            + str(children)
        )

    def handle_operator(
        self,
        token: Token,
        current_operator: str,
        current_negation: bool,
    ) -> typing.Tuple[str, bool]:
        """Handle operators."""

        # Set the current operator to the token
        current_operator = token.value.upper()

        # Set a flag if the token is NOT and change to AND
        if current_operator == "NOT":
            current_negation = True
            current_operator = "AND"

        return current_operator, current_negation

    def combine_subsequent_terms(self) -> None:
        """Combine subsequent terms in the list of tokens."""
        # Combine subsequent terms (without quotes)
        # This would be more challenging in the regex
        # Changed the implementation to combine multiple terms
        combined_tokens: typing.List[Token] = []
        i = 0
        j = 0

        while i < len(self.tokens):
            if len(combined_tokens) > 0:
                if (
                    self.tokens[i].type == TokenTypes.SEARCH_TERM
                    and combined_tokens[j - 1].type == TokenTypes.SEARCH_TERM
                ):
                    combined_token = Token(
                        value=combined_tokens[j - 1].value + " " + self.tokens[i].value,
                        type=TokenTypes.SEARCH_TERM,
                        position=(
                            combined_tokens[j - 1].position[0],
                            self.tokens[i].position[1],
                        ),
                    )
                    combined_tokens.pop()
                    combined_tokens.append(combined_token)
                    i += 1
                    continue

            if (
                i + 1 < len(self.tokens)
                and self.tokens[i].type == TokenTypes.SEARCH_TERM
                and self.tokens[i + 1].type == TokenTypes.SEARCH_TERM
            ):
                combined_token = Token(
                    value=self.tokens[i].value + " " + self.tokens[i + 1].value,
                    type=TokenTypes.SEARCH_TERM,
                    position=(
                        self.tokens[i].position[0],
                        self.tokens[i + 1].position[1],
                    ),
                )
                combined_tokens.append(combined_token)
                i += 2
                j += 1
            else:
                combined_tokens.append(self.tokens[i])
                i += 1
                j += 1

        self.tokens = combined_tokens

    def append_children(
        self,
        children: typing.List[Query],
        sub_query: Query,
        current_operator: str,
    ) -> list:
        """Check where to append the sub expression."""
        if children:
            # Check if the current operator is the same as the last child
            # and if the last child is the same as the last child of the sub expression
            if (
                current_operator == sub_query.value
                and sub_query.value == children[-1].value
            ):
                # Append the children of the sub expression to the last child
                for child in sub_query.children:
                    children[-1].children.append(child)

            # Check if the last child is an operator and the sub expression is a term
            # and the current operator is the same as the last child
            elif (
                current_operator == sub_query.value
                or self.is_term(sub_query.value)
                and self.is_operator(children[0].value)
                and sub_query.children
            ):
                # Append the sub expression to the last child
                for child in sub_query.children:
                    children.append(child)
            # Check if the sub_query is an operator or the sub expression is a term
            # and the current operator is the same as the last child
            elif (
                self.is_operator(sub_query.value) or self.is_term(sub_query.value)
            ) and current_operator == children[0].value:
                # Append the sub expression to the last child
                children[-1].children.append(sub_query)
            else:
                # Append the sub expression to the list of children
                children.append(sub_query)
        else:
            # Append the sub expression to the list of children
            children.append(sub_query)

        return children

    def handle_year_search(
        self, token: Token, children: list, current_operator: str
    ) -> typing.List[Query]:
        """Handle the year search field."""

        search_field = SearchField(
            value=Fields.YEAR,
            position=token.position,
        )

        # Add the year search field to the list of children
        return self.add_term_node(
            index=0,
            value=token.value,
            operator=False,
            search_field=search_field,
            position=token.position,
            children=children,
            current_operator=current_operator,
        )

    # pylint: disable=too-many-arguments
    def add_term_node(
        self,
        *,
        index: int,
        value: str,
        operator: bool,
        search_field: typing.Optional[SearchField] = None,
        position: typing.Optional[tuple] = None,
        current_operator: str = "",
        children: typing.Optional[typing.List[Query]] = None,
        current_negation: bool = False,
    ) -> typing.List[Query]:
        """Adds the term node to the Query"""
        if not children:
            children = []
        # Create a new term node
        term_node = Query(
            value=value, operator=operator, search_field=search_field, position=position
        )

        # Append the term node to the list of children
        if current_operator:
            if (
                not children
                or ((children[-1].value != current_operator) and not current_negation)
                or "NEAR" in current_operator
            ):
                if "NEAR" in current_operator and "NEAR" in children[0].value:
                    current_operator, distance = current_operator.split("/")
                    # Get previous term to append
                    while index > 0:
                        if self.tokens[index - 1].type == TokenTypes.SEARCH_TERM:
                            term_node = Query(
                                value=current_operator,
                                operator=True,
                                children=[
                                    Query(
                                        value=self.tokens[index - 1].value,
                                        operator=False,
                                        search_field=search_field,
                                    ),
                                    term_node,
                                ],
                                distance=int(distance),
                            )
                            break
                        index -= 1

                    children = [
                        Query(
                            value=Operators.AND,
                            operator=True,
                            children=[*children, term_node],
                            search_field=search_field,
                        )
                    ]
                else:
                    children = [
                        Query(
                            value=current_operator,
                            operator=True,
                            children=[*children, term_node],
                            search_field=search_field,
                        )
                    ]
            else:
                children[-1].children.append(term_node)
        else:
            children.append(term_node)

        return children

    def _map_default_field(self, search_field: str) -> str:
        """Get the key of the search field."""
        for key, value_list in WOSSearchFieldList.search_field_dict.items():
            if search_field in value_list:
                translated_field = self.FIELD_TRANSLATION_MAP[key]
                return translated_field
        return search_field

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields."""

        if query.children:
            for child in query.children:
                self.translate_search_fields(child)
            return

        if query.search_field:
            query.search_field.value = self._map_default_field(query.search_field.value)

        # at this point it may be necessary to split (OR)
        # queries for combined search fields
        # see _expand_combined_fields() in pubmed

    def pre_linting(self) -> None:
        """Pre-linting of the query string."""
        # Check if there is an unsolvable error in the query string
        self.query_linter.pre_linting()
        self.fatal_linter_err = any(e["is_fatal"] for e in self.linter_messages)

    def parse(self) -> Query:
        """Parse a query string."""

        self.linter_messages.clear()
        self.tokenize()
        self.add_artificial_parentheses_for_operator_precedence()

        self.pre_linting()

        if not self.fatal_linter_err:
            query, _ = self.parse_query_tree()
            self.translate_search_fields(query)
        else:
            print("\n[FATAL:] Fatal error detected in pre-linting")

        # Print linter messages
        if self.linter_messages:
            if self.mode != LinterMode.STRICT and not self.fatal_linter_err:
                print(
                    "\n[INFO:] The following errors have been corrected by the linter:"
                )

            for msg in self.linter_messages:
                print(
                    "[Linter:] "
                    + msg["label"]
                    + "\t"
                    + msg["message"]
                    + " At position "
                    + str(msg["position"])
                )

            # Raise an exception
            # if the linter is in strict mode
            # or if a fatal error has occurred
            if (
                self.mode == LinterMode.STRICT
                or self.fatal_linter_err
                and self.linter_messages
            ):
                raise FatalLintingException(
                    message="LinterDetected",
                    query_string=self.query_str,
                    linter_messages=self.linter_messages,
                )

        return query


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"
    LIST_ITEM_REFERENCE = r"#\d+"
    OPERATOR_NODE_REGEX = r"#\d+|AND|OR"
    query_dict: dict

    def __init__(self, query_list: str, search_field_general: str, mode: str) -> None:
        super().__init__(
            query_list=query_list,
            parser_class=WOSParser,
            search_field_general=search_field_general,
            mode=mode,
        )

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

    def _check_missing_root(self) -> bool:
        missing_root = False
        # Raise an error if the last item of the list is not the last combining string
        if "#" not in list(self.query_dict.values())[-1]["node_content"]:
            self.add_linter_message(
                QueryErrorCode.MISSING_ROOT_NODE,
                list_position=QueryListParser.GENERAL_ERROR_POSITION,
                position=(-1, -1),
            )
            missing_root = True
        return missing_root

    def _check_missing_operator_nodes(self, missing_root: bool) -> None:
        if missing_root:
            return
        # require combining list items
        if not any("#" in query["node_content"] for query in self.query_dict.values()):
            # If there is no combining list item, raise a linter exception
            # Individual list items can not be connected
            # raise ValueError("[ERROR] No combining list item found.")
            self.add_linter_message(
                QueryErrorCode.MISSING_OPERATOR_NODES,
                list_position=QueryListParser.GENERAL_ERROR_POSITION,
                position=(-1, -1),
            )

    def _check_invalid_list_reference(self) -> None:
        # check if all list-references exist
        for ind, query_node in enumerate(self.query_dict.values()):
            if "#" in query_node["node_content"]:
                # check if all list references exist
                for match in re.finditer(
                    self.LIST_ITEM_REFERENCE, query_node["node_content"]
                ):
                    reference = match.group()
                    position = match.span()
                    if reference.replace("#", "") not in self.query_dict:
                        self.add_linter_message(
                            QueryErrorCode.INVALID_LIST_REFERENCE,
                            list_position=ind,
                            position=position,
                            details=f"List reference {reference} not found.",
                        )

    def _check_query_tokenization(self) -> None:
        for ind, query_node in enumerate(self.query_dict.values()):
            query_parser = WOSParser(
                query_str=query_node["node_content"],
                search_field_general=self.search_field_general,
                mode=self.mode,
            )
            try:
                query_parser.parse()
            except FatalLintingException:  # add more specific message?""
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED,
                    list_position=ind,
                    position=(-1, -1),
                )
            for msg in query_parser.linter_messages:
                if ind not in self.linter_messages:
                    self.linter_messages[ind] = []
                self.linter_messages[ind].append(msg)

    def lint_list_parser(self) -> None:
        """Lint the list parser."""

        try:
            self.query_dict = self.tokenize_list()
        except ValueError:  # may catch other errors here
            self.add_linter_message(
                QueryErrorCode.TOKENIZING_FAILED,
                list_position=QueryListParser.GENERAL_ERROR_POSITION,
                position=(-1, -1),
            )

        missing_root = self._check_missing_root()
        self._check_missing_operator_nodes(missing_root)
        self._check_invalid_list_reference()
        self._check_query_tokenization()

        self.fatal_linter_err = any(
            d["is_fatal"] for e in self.linter_messages.values() for d in e
        )
        if self.fatal_linter_err:
            print("\n[FATAL:] Fatal error detected in pre-linting")
            # Print linter messages
            if self.mode != LinterMode.STRICT and not self.fatal_linter_err:
                print(
                    "\n[INFO:] The following errors have been corrected by the linter:"
                )

            for level, message_list in self.linter_messages.items():
                print(f"\n[INFO:] Linter messages for level {level}:")
                for msg in message_list:
                    print(
                        "[Linter:] "
                        + msg["label"]
                        + "\t"
                        + msg["message"]
                        + " At position "
                        + str(msg["position"])
                    )

            # Raise an exception
            # if the linter is in strict mode
            # or if a fatal error has occurred
            if (
                self.mode == LinterMode.STRICT
                or self.fatal_linter_err
                and self.linter_messages
            ):
                l_messages = [
                    y for x in self.linter_messages.values() if x for y in x if y
                ]
                raise FatalLintingException(
                    message="LinterDetected",
                    query_string=self.query_list,
                    linter_messages=l_messages,
                )

    def _build_query_from_operator_node(self, tokens: list) -> Query:
        operator = ""
        children = []
        for token in tokens:
            if "#" in token.value:
                idx = token.value.replace("#", "")  # - 1
                children.append(self.query_dict[idx]["query"])
            else:
                if not operator:
                    operator = token.value
                elif operator != token.value:
                    raise ValueError(
                        "[ERROR] Two different operators used in the same line."
                    )

        assert operator, "[ERROR] No operator found in combining query."

        operator_query = Query(
            value=operator,
            operator=True,
            children=children,
        )
        return operator_query

    def _parse_queries(self) -> typing.Tuple[typing.List[Query], dict]:
        """Parse the queries from the list of queries."""
        queries: typing.List[Query] = []
        operator_nodes = {}

        for node_nr, node_content in self.query_dict.items():
            if "#" in node_content["node_content"]:
                operator_nodes[node_nr] = node_content["node_content"]
                queries.append(Query("Filler for combine queries"))
            else:
                query_parser = WOSParser(
                    query_str=node_content["node_content"],
                    search_field_general=self.search_field_general,
                    mode=self.mode,
                )
                query = query_parser.parse()
                queries.append(query)
        return queries, operator_nodes

    def _parse_list_query(self) -> Query:

        for node_nr, node_content in self.query_dict.items():
            if node_content["type"] == ListTokenTypes.QUERY_NODE:
                query_parser = WOSParser(
                    query_str=node_content["node_content"],
                    search_field_general=self.search_field_general,
                    mode=self.mode,
                )
                query = query_parser.parse()
                node_content["query"] = query

            elif node_content["type"] == ListTokenTypes.OPERATOR_NODE:
                tokens = self.tokenize_operator_node(
                    node_content["node_content"], node_nr
                )
                self._validate_tokens(tokens, node_nr)
                query = self._build_query_from_operator_node(tokens)
                self.query_dict[node_nr]["query"] = query

        return list(self.query_dict.values())[-1]["query"]

    def parse(self) -> Query:
        """Parse the list of queries."""

        self.lint_list_parser()

        # Print linter messages
        if self.linter_messages:
            if self.mode != LinterMode.STRICT and not self.fatal_linter_err:
                print(
                    "\n[INFO:] The following errors have been corrected by the linter:"
                )
            for level, linter_messages in self.linter_messages.items():
                for msg in linter_messages:
                    print(
                        "[Linter:] "
                        + msg["label"]
                        + "\t"
                        + msg["message"]
                        + " At position "
                        + str(msg["position"])
                        + f"(level {level})"
                    )

                # Raise an exception
                # if the linter is in strict mode
                # or if a fatal error has occurred
                if (
                    self.mode == LinterMode.STRICT
                    or self.fatal_linter_err
                    and linter_messages
                ):
                    raise FatalLintingException(
                        message="LinterDetected",
                        query_string="",  # add query-string?
                        linter_messages=linter_messages,
                    )

        self.tokenize_list()
        query = self._parse_list_query()
        return query

    def tokenize_operator_node(self, query_str: str, node_nr: int) -> list:
        """Tokenize the query_list."""

        tokens = []
        for match in re.finditer(self.OPERATOR_NODE_REGEX, query_str):
            value = match.group()
            position = match.span()
            if re.fullmatch(self.LIST_ITEM_REFERENCE, value):
                token_type = OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
            elif re.fullmatch(WOSParser.LOGIC_OPERATOR_REGEX, value):
                token_type = OperatorNodeTokenTypes.LOGIC_OPERATOR
            else:
                token_type = OperatorNodeTokenTypes.UNKNOWN
            tokens.append(
                ListToken(
                    value=value, type=token_type, level=node_nr, position=position
                )
            )

        return tokens

    def _validate_tokens(self, tokens: list, node_nr: int) -> None:
        """Validate the tokens of the combining list element."""
        for token in tokens:
            if token.type == OperatorNodeTokenTypes.UNKNOWN:
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED,
                    list_position=QueryListParser.GENERAL_ERROR_POSITION,
                    position=token.position,
                )

        # Note: details should pass "format should be #1 [operator] #2"

        # Must start with LIST_ITEM
        if tokens[0].type != OperatorNodeTokenTypes.LIST_ITEM_REFERENCE:
            self.add_linter_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                list_position=QueryListParser.GENERAL_ERROR_POSITION,
                position=tokens[0].position,
                details=f"First token for query item {node_nr} must be a list item.",
            )
            return

        # Expect alternating pattern after first LIST_ITEM
        expected = OperatorNodeTokenTypes.LOGIC_OPERATOR
        for _, token in enumerate(tokens[1:], start=1):
            if token.type != expected:
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    list_position=QueryListParser.GENERAL_ERROR_POSITION,
                    position=token.position,
                    details=f"Expected {expected.name} for query item {node_nr} "
                    f"at position {token.position}, but found {token.type.name}.",
                )
                return
            # Alternate between LOGIC_OPERATOR and LIST_ITEM
            expected = (
                OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
                if expected == OperatorNodeTokenTypes.LOGIC_OPERATOR
                else OperatorNodeTokenTypes.LOGIC_OPERATOR
            )

        # The final token must be a LIST_ITEM (if even-length list of tokens)
        if expected == OperatorNodeTokenTypes.LIST_ITEM_REFERENCE:
            self.add_linter_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                list_position=QueryListParser.GENERAL_ERROR_POSITION,
                position=tokens[-1].position,
                details=f"Last token of query item {node_nr} must be a list item.",
            )
