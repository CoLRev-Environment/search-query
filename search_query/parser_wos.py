#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import Fields
from search_query.constants import LinterMode
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
        search_fields: str = "",
        mode: str = LinterMode.STRICT,
    ) -> None:
        """Initialize the parser."""
        super().__init__(query_str=query_str, search_fields=search_fields, mode=mode)
        self.query_linter = QueryLinter(parser=self)

    def tokenize(self) -> None:
        """Tokenize the query_str."""

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
                self.add_linter_message(QueryErrorCode.TOKENIZING_FAILED, position)
                continue

            self.tokens.append(Token(value=value, type=token_type, position=position))

        self.combine_subsequent_terms()

    # Implement and override methods of parent class (as needed)
    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return (
            bool(re.match(self.SEARCH_FIELD_REGEX, token))
            or token in WOSSearchFieldList.language_list
        )

    def parse_query_tree(
        self,
        tokens: list,
    ) -> Query:
        """Parse a query from a list of tokens."""

        # Search fields are given in the search_fields string
        if self.search_fields:
            found_list = []
            print("\n[Info:] Search Fields given: " + self.search_fields)
            matches = re.findall(self.SEARCH_FIELDS_REGEX, self.search_fields)

            for match in matches:
                match = self.check_search_fields(
                    match,
                )

                # Check if the search field is not in the list of search fields
                if match not in found_list:
                    self.search_fields_list.append(
                        SearchField(value=match, position=None)
                    )
                    found_list.append(match)
                    print("[Info:] Search Field accepted: " + match)

        # Parse a query tree from tokens recursively
        def parse_expression(
            tokens: list,
            index: int,
            search_field: typing.Optional[SearchField] = None,
            superior_search_field: typing.Optional[SearchField] = None,
            current_negation: bool = False,
        ) -> typing.Tuple[Query, int]:
            """Parse tokens starting at the given index,
            handling parentheses, operators, search fields and terms recursively."""
            children = []
            current_operator = None

            if current_negation:
                current_operator = "NOT"

            while index < len(tokens):
                token = tokens[index]

                # Handle nested expressions within parentheses
                if token.type == TokenTypes.PARENTHESIS_OPEN:
                    if tokens[index - 1].type == TokenTypes.FIELD:
                        superior_search_field = tokens[index - 1].value

                    # Parse the expression inside the parentheses
                    sub_expr, index = parse_expression(
                        tokens=tokens,
                        index=index + 1,
                        search_field=search_field,
                        superior_search_field=superior_search_field,
                        current_negation=current_negation,
                    )

                    if isinstance(sub_expr, list):
                        # Add all children from the parsed expression
                        # to the list of children
                        for child in sub_expr:
                            children = self.append_children(
                                children=children,
                                sub_expr=child,
                                current_operator=current_operator,
                            )
                    else:
                        # Add the parsed expression to the list of children
                        children = self.append_children(
                            children=children,
                            sub_expr=sub_expr,
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
                    # Safe the children if there is a change
                    # of operator within the current parentheses
                    if current_operator and current_operator != token.upper():
                        children = self.safe_children(
                            children=children,
                            current_operator=current_operator,
                        )

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
                elif (self.is_search_field(token)) or (
                    token in WOSSearchFieldList.language_list
                ):
                    search_field = SearchField(
                        value=token.value, position=token.position
                    )

                # Handle terms
                else:
                    # Check if the token is a search field which has constraints
                    # Check if the token is a year
                    if re.findall(self.YEAR_REGEX, token):
                        if search_field.value in WOSSearchFieldList.year_published_list:
                            children = self.handle_year_search(
                                token, children, current_operator
                            )
                            index += 1
                            continue
                        # Year detected without search field
                        print(
                            "[INFO:] Year detected "
                            "without search field at position " + str(token.position)
                        )

                    # Set search field to superior search field
                    # if no search field is given
                    if not search_field and superior_search_field:
                        search_field = superior_search_field

                    # Set search field to ALL if no search field is given
                    if not search_field:
                        search_field = SearchField("All", position=None)

                    # Check if the token is ISSN or ISBN
                    if search_field.value in WOSSearchFieldList.issn_isbn_list:
                        if self.query_linter.check_issn_isbn_format(token=token):
                            self.fatal_linter_err = True

                    # Check if the token is a doi
                    if search_field.value in WOSSearchFieldList.doi_list:
                        if self.query_linter.check_doi_format(token=token):
                            self.fatal_linter_err = True

                    # Add term nodes
                    children = self.add_term_node(
                        tokens=tokens,
                        index=index,
                        value=token,
                        operator=False,
                        search_field=search_field,
                        position=token.position,
                        children=children,
                        current_operator=current_operator,
                        current_negation=current_negation,
                    )

                    current_operator = None
                    search_field_for_check = None

                    if isinstance(search_field, SearchField):
                        search_field_for_check = search_field.value
                    else:
                        search_field_for_check = search_field

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
                    Query(value=current_operator, operator=True, children=children),
                    index,
                )

            # Return the children if there are multiple children
            if self.is_operator(children[0].value):
                # Check if the operator of the first child
                # is not the same as the second child
                if children[0].value != children[1].value:
                    for child in children:
                        if not children.index(child) == 0:
                            # Check if the search field is in the language/year list
                            if children[children.index(child)].search_field.value and (
                                children[children.index(child)].search_field.value
                                in WOSSearchFieldList.language_list
                                or children[children.index(child)].search_field.value
                                in WOSSearchFieldList.year_published_list
                            ):
                                children[0].children.append(child)
                                children.pop(children.index(child))
                    return children[0], index

                # Check if the operator of the first child is the same
                # as the second child
                if children[0].value == children[1].value:
                    operator_children = []
                    for child in children:
                        for grandchild in child.children:
                            operator_children.append(grandchild)

                    return (
                        Query(
                            value=children[0].value,
                            operator=True,
                            children=operator_children,
                        ),
                        index,
                    )

            # Raise an error if the code gets here
            raise NotImplementedError("Error in parsing the query tree")

        root_query, _ = parse_expression(tokens=tokens, index=0, search_field=None)
        return root_query

    def handle_closing_parenthesis(
        self,
        children: list,
        current_operator: str,
    ):
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
        # Return the children if there are multiple children
        return children

    def handle_operator(
        self,
        token: Token,
        current_operator: str,
        current_negation: bool,
    ):
        """Handle operators."""

        # Set the current operator to the token
        current_operator = token.value.upper()

        # Add linter messages for operators that are not uppercase
        if token.value.islower():
            self.add_linter_message(
                QueryErrorCode.OPERATOR_CAPITALIZATION, pos=token.position
            )

        # Set default near_distance if not set in the search string
        if current_operator == "NEAR":
            # Add linter message for NEAR operator without distance
            self.add_linter_message(
                QueryErrorCode.IMPLICIT_NEAR_VALUE, pos=token.position
            )
            current_operator = "NEAR/15"

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
        combined_tokens = []
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
        children: list,
        sub_expr: Query,
        current_operator: str,
    ) -> list:
        """Check where to append the sub expression."""
        if children:
            # Check if the current operator is the same as the last child
            # and if the last child is the same as the last child of the sub expression
            if (
                current_operator == sub_expr.value
                and sub_expr.value == children[-1].value
            ):
                # Append the children of the sub expression to the last child
                for child in sub_expr.children:
                    children[-1].children.append(child)

            # Check if the last child is an operator and the sub expression is a term
            # and the current operator is the same as the last child
            elif (
                current_operator == sub_expr.value
                or self.is_term(sub_expr.value)
                and self.is_operator(children[0].value)
                and sub_expr.children
            ):
                # Append the sub expression to the last child
                for child in sub_expr.children:
                    children.append(child)
            # Check if the sub_expr is an operator or the sub expression is a term
            # and the current operator is the same as the last child
            elif (
                self.is_operator(sub_expr.value) or self.is_term(sub_expr.value)
            ) and current_operator == children[0].value:
                # Append the sub expression to the last child
                children[-1].children.append(sub_expr)
            else:
                # Append the sub expression to the list of children
                children.append(sub_expr)
        else:
            # Append the sub expression to the list of children
            children.append(sub_expr)

        return children

    def handle_year_search(
        self, token: Token, children: list, current_operator: str
    ) -> list:
        """Handle the year search field."""
        # Check if a wildcard is used in the year search field
        if any(char in token.value for char in ["*", "?", "$"]):
            self.add_linter_message(
                QueryErrorCode.WILDCARD_IN_YEAR,
                pos=token.position,
            )
            # TODO : use any(x.is_fatal() for x in QueryErrorCodes)

        # Check if the yearspan is not more than 5 years
        if len(token.value) > 4:
            if int(token.value[5:9]) - int(token.value[0:4]) > 5:
                # Change the year span to five years
                token.value = str(int(token.value[5:9]) - 5) + "-" + token.value[5:9]

                self.add_linter_message(
                    QueryErrorCode.YEAR_SPAN_VIOLATION, pos=token.position
                )

        search_field = SearchField(
            value=Fields.YEAR,
            position=token.position,
        )

        # Add the year search field to the list of children
        return self.add_term_node(
            tokens=[],
            index=0,
            value=token.value,
            operator=False,
            search_field=search_field,
            position=token.position,
            children=children,
            current_operator=current_operator,
        )

    def add_term_node(
        self,
        tokens: list,
        index: int,
        value: str,
        operator: bool,
        search_field: typing.Optional[SearchField] = None,
        position: typing.Optional[tuple] = None,
        current_operator: str = None,
        children: typing.Optional[typing.List[typing.Union[str, Query]]] = None,
        current_negation: bool = False,
    ) -> typing.Optional[typing.List[typing.Union[str, Query]]]:
        """Adds the term node to the Query"""

        # Create a new term node
        term_node = Query(
            value=value, operator=operator, search_field=search_field, position=position
        )

        # Append the term node to the list of children
        if current_operator:
            if (
                not children
                or (
                    (
                        isinstance(children[-1], Query)
                        and (children[-1].value != current_operator)
                    )
                    and not current_negation
                )
                or "NEAR" in current_operator
            ):
                if "NEAR" in current_operator and "NEAR" in children[0].value:
                    # Get previous term to append
                    while index > 0:
                        if tokens[index - 1].type == TokenTypes.SEARCH_TERM:
                            term_node = Query(
                                value=current_operator,
                                operator=True,
                                children=[
                                    Query(
                                        value=tokens[index - 1].value,
                                        operator=False,
                                        search_field=search_field,
                                    ),
                                    term_node,
                                ],
                            )
                            break
                        index -= 1

                    children = [
                        Query(
                            value=Operators.AND,
                            operator=True,
                            children=[*children, term_node],
                        )
                    ]
                else:
                    children = [
                        Query(
                            value=current_operator,
                            operator=True,
                            children=[*children, term_node],
                        )
                    ]
            else:
                children[-1].children.append(term_node)
        else:
            children.append(term_node)

        return children

    def translate_search_fields(self, query: Query) -> Query:
        """Translate search fields."""

        children = []

        # Recursively translate the search fields of child nodes
        if query.children:
            for child in query.children:
                children.append(self.translate_search_fields(child))
            query.children = children

        translated_field = None
        query_search_field_list = []
        if query.search_field:
            # Check given Search Fields from JSON
            if self.search_fields_list:
                self.check_search_fields_from_json(
                    search_field=query.search_field, position=query.position
                )

                if query.search_field.value == "Misc" and self.search_fields_list:
                    for search_field_item in self.search_fields_list:
                        if search_field_item.value == "Misc":
                            search_field_item.value = Fields.ALL
                            self.add_linter_message(
                                QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                                # note='Set to "ALL=".',
                                pos=query.position,
                            )

                        query.search_field = search_field_item

                        if isinstance(search_field_item.value, str):
                            translated_field = self.FIELD_TRANSLATION_MAP.get(
                                search_field_item.value, None
                            )

                        # Translate only if a mapping exists
                        # else use default search field [ALL=]
                        if translated_field:
                            query.search_field = translated_field

                            # Just print the message because search fields
                            # in "xx" format are not supported
                            print(
                                "[INFO:] Search Field "
                                + translated_field
                                + " has been detected."
                                + " At the position "
                                + str(query.position)
                            )

                        query_search_field_list.append(
                            Query(
                                value=query.value,
                                operator=False,
                                position=query.position,
                                search_field=query.search_field,
                            )
                        )

                        # TODO : let's discuss this to make sure the message is correct.
                        self.add_linter_message(
                            QueryErrorCode.SEARCH_FIELD_NOT_FOUND,
                            # msg="Search Fields have been extracted from JSON.",
                            pos=query.position,
                        )

                    if len(query_search_field_list) > 1:
                        query = Query(
                            value=Operators.OR,
                            operator=True,
                            children=query_search_field_list,
                        )

            if not query.operator:
                original_field = self.check_search_fields(query.search_field)
                if isinstance(original_field, str):
                    translated_field = self.FIELD_TRANSLATION_MAP.get(
                        original_field, None
                    )

                # Translate only if a mapping exists
                # else use default search field [ALL=]
                if translated_field:
                    query.search_field = translated_field

                    # Just print the message because search fields
                    # in "xx" format are not supported
                    print(
                        "[INFO:] Search Field "
                        + translated_field
                        + " has been detected."
                        + " At the position "
                        + str(query.position)
                    )
                else:
                    self.add_linter_message(
                        # TODO : check whether this is accurate:
                        # msg="Search Field not set or not supported."
                        # fix= Using default of the database (ALL)
                        QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                        pos=query.position,
                    )
                    query.search_field = Fields.ALL

        if not query.search_field and not translated_field and not query.operator:
            query.search_field = Fields.ALL

            self.add_linter_message(
                QueryErrorCode.SEARCH_FIELD_NOT_FOUND,
                # msg='Set to "ALL=".',
                pos=query.position,
            )

        return query

    def check_search_fields(self, search_field) -> str:
        """Translate a search field into base search field."""
        if isinstance(search_field, SearchField):
            search_field = search_field.value

        # Check if the given search field is in one of the lists of search fields
        return self.get_search_field_key(search_field=search_field)

    def get_search_field_key(self, search_field: str) -> str:
        """Get the key of the search field."""
        for key, value_list in WOSSearchFieldList.search_field_dict.items():
            if search_field in value_list:
                return key
        return "Misc"

    def check_search_fields_from_json(
        self,
        search_field: str,
        position: tuple,
    ) -> None:
        """Check if the search field is in the list of search fields from JSON."""
        if isinstance(search_field, SearchField):
            search_field = search_field.value

        if not search_field == "Misc":
            diffrent_search_field = []
            for search_field_item in self.search_fields_list:
                if search_field == search_field_item.value:
                    # TODO : warning (message) for linter?
                    print(
                        "[INFO:] Data redudancy. "
                        "Same Search Field in Search and Search Fields."
                    )

                if self.check_search_fields(search_field) == self.check_search_fields(
                    search_field_item.value
                ):
                    diffrent_search_field.append("False")
                else:
                    diffrent_search_field.append("True")

            if "False" not in diffrent_search_field:
                self.add_linter_message(
                    QueryErrorCode.SEARCH_FIELD_NOT_FOUND,
                    pos=position,
                )

    def safe_children(self, children: list, current_operator: str) -> list:
        """Safe children, when there is a change of
        operator within the current parentheses."""
        safe_children = []
        safe_children.append(
            Query(
                value=current_operator,
                operator=True,
                children=children,
            )
        )

        return safe_children

    def check_nested_operators(self, query: Query) -> Query:
        """Check if there are double nested operators."""
        del_children = []

        if query.operator:
            for child in query.children:
                if child.operator:
                    if child.value == query.value:
                        # Get the child one level up
                        for grandchild in child.children:
                            query.children.append(grandchild)
                        del_children.append(query.children.index(child))

            # Delete the child
            if del_children:
                del_children.reverse()
                for index in del_children:
                    query.children.pop(index)

        if query.children:
            for child in query.children:
                self.check_nested_operators(child)
        return query

    def pre_linting(self) -> None:
        """Pre-linting of the query string."""
        # Check if there is an unsolvable error in the query string
        self.query_linter.pre_linting()
        self.fatal_linter_err = any(e.is_fatal() for e in self.linter_messages)

    # Note: never called?
    # def insert_parentheses(self, tokens, index, span) -> None:
    #     """Insert parentheses in the query string."""
    #     first_parenthesis_inserted = False
    #     last_parenthesis_inserted = False
    #     # Find previous operator
    #     for i in range(index - 1, 0, -1):
    #         if self.is_operator(tokens[i][0]):
    #             self.tokens.insert(
    #                 i + 1, ("(", (tokens[i][1][1] + 1, tokens[i][1][1] + 2))
    #             )
    #             first_parenthesis_inserted = True
    #             break
    #     # Find next operator
    #     for i in range(index + 2, len(tokens)):
    #         if self.is_operator(tokens[i][0]):
    #             self.tokens.insert(
    #                 i - 1, (")", (tokens[i][1][1] - 2, tokens[i][1][1] - 1))
    #             )
    #             last_parenthesis_inserted = True
    #             break

    #     if not first_parenthesis_inserted:
    #         self.tokens.insert((0, ("(", (0, 1))))

    #     if not last_parenthesis_inserted:
    #         self.tokens.append((")", (span[1] + 1, span[1] + 2)))

    def parse(self) -> Query:
        """Parse a query string."""
        # Remove all previous linter messages
        self.linter_messages.clear()

        # Tokenize the query string
        self.tokenize()

        # Pre-linting of the query string
        self.pre_linting()

        if not self.fatal_linter_err:
            # Parse the query string, build the query tree and translate search fields
            query = self.parse_query_tree(self.tokens)
            query = self.translate_search_fields(query)
            query = self.check_nested_operators(query)
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
                    + msg["rule"]
                    + "\t"
                    + msg["message"]
                    + " At position "
                    + str(msg["position"])
                )

            # Raise an exception
            # if the linter is in strict mode
            # or if a fatal error has occurred
            if self.mode == "strict" or self.fatal_linter_err and self.linter_messages:
                raise FatalLintingException(
                    message="LinterDetected",
                    query_string=self.query_str,
                    linter_messages=self.linter_messages,
                )

        return query


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"
    LIST_COMBINE_REGEX = r"#\d+|AND|OR"

    def __init__(self, query_list: str, search_fields: str, linter_mode: str) -> None:
        super().__init__(query_list, WOSParser, search_fields, linter_mode)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

    def parse(self) -> Query:
        """Parse the list of queries."""
        # the parse() method of QueryListParser is called to parse the list of queries
        query_dict = self.parse_dict()
        queries = []
        combine_queries = {}

        for node_nr, node_content in query_dict.items():
            if node_nr == "14":
                print(node_content["node_content"])

            if "#" in node_content["node_content"]:
                combine_queries[node_nr] = node_content["node_content"]
                queries.append("Filler for combine queries")
            else:
                query_parser = self.parser_class(
                    query_str=node_content["node_content"],
                    search_fields=self.search_fields,
                    mode=self.linter_mode,
                )
                query = query_parser.parse()
                queries.append(query)

        # If there is no combining list item, raise a linter exception
        # Individual list items can not be connected
        if not combine_queries:
            raise ValueError("[ERROR] No combining list item found.")

        # Raise an error if the last item of the list is not the last combining string
        if not (
            combine_queries[str(len(query_dict))]
            == query_dict[str(len(query_dict))]["node_content"]
        ):
            raise ValueError(
                "[ERROR] The last item of the list must be a combining string."
                + "\nFound: "
                + query
            )

        for index, query in combine_queries.items():
            children = []
            res_children = []
            operator = None
            tokens = self.tokenize_combining_list_elem(query)

            # Check if the last token is a operator
            if tokens[len(tokens) - 1] in ["AND", "OR"]:
                raise ValueError(
                    "[ERROR] The last token of a combining list item must be a number."
                    + "\nFound: "
                    + query
                    + "\nFor combinations like this '#4 AND DT=(Article)'"
                    + " split the query into two seperate list items and"
                    + " add them together in the next list item:"
                    + "\n 5. DT=(Article)"
                    + "\n 6. #4 AND #5"
                )

            # Check if the last token is a number
            # This error is never raised
            # because the regex only matches numbers and operators
            if "#" not in tokens[len(tokens) - 1]:
                raise ValueError(
                    "[ERROR] LastTokenMustBeNumber\t"
                    + "Combining list item must be a number. No term, language or year."
                    + "\nFound: "
                    + tokens[len(tokens) - 1]
                )

            for token in tokens:
                if "#" in token:
                    token = token.replace("#", "")
                    children.append(queries[int(token) - 1])
                else:
                    if not operator or operator == token:
                        operator = token
                    else:
                        raise ValueError(
                            "[ERROR] Two different operators are used in one line."
                        )

            for child in children:
                if child.value == operator:
                    for grandchild in child.children:
                        res_children.append(grandchild)
                else:
                    res_children.append(child)

            queries[int(index) - 1] = Query(
                value=operator, operator=True, children=res_children
            )

        return queries[len(queries) - 1]

    def tokenize_combining_list_elem(self, query_str: str) -> list:
        """Tokenize the query_list."""
        matches = re.findall(self.LIST_COMBINE_REGEX, query_str)
        return matches
