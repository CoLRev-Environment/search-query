#!/usr/bin/env python3
"""Web-of-Science query linter."""
import re
import typing

from search_query.constants import GENERAL_ERROR_POSITION
from search_query.constants import ListTokenTypes
from search_query.constants import OperatorNodeTokenTypes
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.linter_base import QueryListLinter
from search_query.linter_base import QueryStringLinter
from search_query.query import Query
from search_query.wos.constants import syntax_str_to_generic_search_field_set
from search_query.wos.constants import VALID_FIELDS_REGEX
from search_query.wos.constants import YEAR_PUBLISHED_FIELD_REGEX

if typing.TYPE_CHECKING:  # pragma: no cover
    import search_query.wos.parser


class WOSQueryStringLinter(QueryStringLinter):
    """Linter for WOS Query Strings"""

    ISSN_VALUE_REGEX = re.compile(r"^\d{4}-\d{3}[\dX]$", re.IGNORECASE)
    ISBN_VALUE_REGEX = re.compile(
        r"^(?:\d{1,5}-\d{1,7}-\d{1,7}-[\dX]|\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1})$",
        re.IGNORECASE,
    )
    DOI_VALUE_REGEX = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
    YEAR_VALUE_REGEX = re.compile(r"^\d{4}(-\d{4})?$")

    WILDCARD_CHARS = ["?", "$", "*"]

    VALID_FIELDS_REGEX = VALID_FIELDS_REGEX

    PLATFORM: PLATFORM = PLATFORM.WOS

    VALID_TOKEN_SEQUENCES = {
        TokenTypes.FIELD: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.SEARCH_TERM: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PROXIMITY_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.LOGIC_OPERATOR: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.FIELD,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.PROXIMITY_OPERATOR: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
            TokenTypes.FIELD,
        ],
        TokenTypes.PARENTHESIS_OPEN: [
            TokenTypes.FIELD,
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.PARENTHESIS_CLOSED: [
            TokenTypes.PARENTHESIS_CLOSED,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PROXIMITY_OPERATOR,
        ],
    }

    def __init__(self, query_str: str = "") -> None:
        super().__init__(query_str=query_str)

    def validate_tokens(
        self,
        *,
        tokens: typing.List[Token],
        query_str: str,
        search_field_general: str = "",
    ) -> typing.List[Token]:
        """Performs a pre-linting"""

        self.tokens = tokens
        self.query_str = query_str
        self.search_field_general = search_field_general

        self.check_invalid_syntax()
        self.check_missing_tokens()
        self.check_unknown_token_types()
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()

        self.check_invalid_characters_in_search_term("@%$^~\\<>{}()[]#")
        # Note : "&" is allowed for journals (e.g., "Information & Management")
        # When used for search terms, it seems to be translated to "AND"
        self.check_near_distance_in_range(max_value=15)
        self.check_search_fields_from_json()
        self.check_implicit_near()
        return self.tokens

    def check_invalid_syntax(self) -> None:
        """Check for invalid syntax in the query string."""

        # Check for erroneous field syntax
        match = re.search(r"\[[A-Za-z]*\]", self.query_str)
        if match:
            self.add_linter_message(
                QueryErrorCode.INVALID_SYNTAX,
                positions=[match.span()],
                details="WOS fields must be before search terms and "
                "without brackets, e.g. AB=robot or TI=monitor. "
                f"'{match.group(0)}' is invalid.",
            )

    def syntax_str_to_generic_search_field_set(self, field_value: str) -> set:
        return syntax_str_to_generic_search_field_set(field_value)

    def check_year_without_search_terms(self, query: Query) -> None:
        """Check if the year is used without a search terms."""

        if query.is_term():
            if not query.search_field:
                return

            if not YEAR_PUBLISHED_FIELD_REGEX.match(query.search_field.value):
                return

            positions = []
            if self.tokens:
                positions = [
                    (
                        self.tokens[0].position[0],
                        self.tokens[-1].position[1],
                    )
                ]
            # Year detected without other search fields
            self.add_linter_message(
                QueryErrorCode.YEAR_WITHOUT_SEARCH_TERMS, positions=positions
            )

    def check_search_fields_from_json(
        self,
    ) -> None:
        """Check if the search field is in the list of search fields from JSON."""

        for index, token in enumerate(self.tokens):
            if token.type not in [TokenTypes.FIELD, TokenTypes.PARENTHESIS_OPEN]:
                if self.search_field_general == "":
                    self.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_MISSING,
                        positions=[(-1, -1)],
                    )
                break

            if token.type == TokenTypes.FIELD:
                if index == 0 and self.search_field_general != "":
                    if token.value != self.search_field_general:
                        self.add_linter_message(
                            QueryErrorCode.SEARCH_FIELD_CONTRADICTION,
                            positions=[token.position],
                        )
                    else:
                        # Note : in basic search, when starting the query with a field,
                        # WOS raises a syntax error.
                        self.add_linter_message(
                            QueryErrorCode.SEARCH_FIELD_REDUNDANT,
                            positions=[token.position],
                        )

                # break: only consider the first FIELD
                # (which may come after parentheses)
                break

    def check_implicit_near(self) -> None:
        """Check for implicit NEAR operator."""
        for token in self.tokens:
            if token.value == "NEAR":
                self.add_linter_message(
                    QueryErrorCode.IMPLICIT_NEAR_VALUE,
                    positions=[token.position],
                )
                token.value = "NEAR/15"

    def check_year_format(self, query: Query) -> None:
        """Check for the correct format of year."""

        if query.is_term():
            if not query.search_field:
                return
            if not YEAR_PUBLISHED_FIELD_REGEX.match(query.search_field.value):
                return
            if any(char in query.value for char in ["*", "?", "$"]):
                self.add_linter_message(
                    QueryErrorCode.WILDCARD_IN_YEAR,
                    positions=[query.position or (-1, -1)],
                )
                return

            if not self.YEAR_VALUE_REGEX.match(query.value):
                self.add_linter_message(
                    QueryErrorCode.YEAR_FORMAT_INVALID,
                    positions=[query.position or (-1, -1)],
                )
                return

            # Check if the yearspan is not more than 5 years
            if len(query.value) > 4:
                if int(query.value[5:9]) - int(query.value[0:4]) > 5:
                    # Change the year span to five years
                    query.value = (
                        str(int(query.value[5:9]) - 5) + "-" + query.value[5:9]
                    )

                    self.add_linter_message(
                        QueryErrorCode.YEAR_SPAN_VIOLATION,
                        positions=[query.position or (-1, -1)],
                    )

        for child in query.children:
            self.check_year_format(child)

    def check_invalid_token_sequences(self) -> None:
        """Check for the correct order of tokens in the query."""

        tokens = self.tokens
        for index in range(len(tokens) - 1):
            token = tokens[index]
            next_token = tokens[index + 1]

            # Skip known exceptions like NEAR proximity modifier (custom rule)
            if (
                token.type == TokenTypes.SEARCH_TERM
                and next_token.value == "("
                and index > 0
                and tokens[index - 1].value.upper() == "NEAR"
            ):
                continue

            # Allow known languages after parenthesis (custom rule)
            if token.value == ")" and YEAR_PUBLISHED_FIELD_REGEX.match(
                next_token.value
            ):
                continue

            # Two operators in a row
            if token.is_operator() and next_token.is_operator():
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    positions=[(token.position[0], next_token.position[1])],
                    details="Two operators in a row are not allowed.",
                )
                continue

            # Two search fields in a row
            if token.type == TokenTypes.FIELD and next_token.type == TokenTypes.FIELD:
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    positions=[next_token.position],
                )
                continue

            # Check transition
            allowed_next_types = self.VALID_TOKEN_SEQUENCES.get(token.type, [])
            if next_token.type not in allowed_next_types:
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    positions=[next_token.position],
                )

    def check_unsupported_wildcards(self, query: Query) -> None:
        """Check for unsupported characters in the search string."""

        if query.is_term():
            # Web of Science does not support "!"
            for match in re.finditer(r"\!+", query.value):
                position = (-1, -1)
                if query.position:
                    position = (
                        query.position[0] + match.start(),
                        query.position[0] + match.end(),
                    )
                self.add_linter_message(
                    QueryErrorCode.WILDCARD_UNSUPPORTED,
                    positions=[position],
                )

        for child in query.children:
            self.check_unsupported_wildcards(child)

    def check_wildcards(self, query: Query) -> None:
        """Check for the usage of wildcards in the search string."""

        if query.is_term():
            value = query.value.replace('"', "")

            # Implement constrains from Web of Science for Wildcards
            for index, charachter in enumerate(value):
                if charachter in self.WILDCARD_CHARS:
                    # Check if wildcard is left or right-handed or standalone
                    if index == 0 and len(value) == 1:
                        self.add_linter_message(
                            QueryErrorCode.WILDCARD_STANDALONE,
                            positions=[query.position or (-1, -1)],
                        )

                    elif len(value) == index + 1:
                        # Right-hand wildcard
                        self.check_unsupported_right_hand_wildcards(
                            query=query, index=index
                        )

                    elif index == 0 and len(value) > 1:
                        # Left-hand wildcard
                        self.check_format_left_hand_wildcards(query)

                    else:
                        # Wildcard in the middle of the term
                        if value[index - 1] in [
                            "/",
                            "@",
                            "#",
                            ".",
                            ":",
                            ";",
                            "!",
                        ]:
                            self.add_linter_message(
                                QueryErrorCode.WILDCARD_AFTER_SPECIAL_CHAR,
                                positions=[query.position or (-1, -1)],
                            )

        for child in query.children:
            self.check_wildcards(child)

    def check_unsupported_right_hand_wildcards(self, query: Query, index: int) -> None:
        """Check for unsupported right-hand wildcards in the search string."""

        if query.value[index - 1] in ["/", "@", "#", ".", ":", ";", "!"]:
            self.add_linter_message(
                QueryErrorCode.WILDCARD_AFTER_SPECIAL_CHAR,
                positions=[query.position or (-1, -1)],
            )

        if len(query.value) < 4:
            self.add_linter_message(
                QueryErrorCode.WILDCARD_RIGHT_SHORT_LENGTH,
                positions=[query.position or (-1, -1)],
            )

    def check_format_left_hand_wildcards(self, query: Query) -> None:
        """Check for wrong usage among left-hand wildcards in the search string."""

        if len(query.value) < 4:
            self.add_linter_message(
                QueryErrorCode.WILDCARD_LEFT_SHORT_LENGTH,
                positions=[query.position or (-1, -1)],
            )

    def check_issn_isbn_format(self, query: "Query") -> None:
        """Check for the correct format of ISSN and ISBN."""

        if query.is_term():
            if not query.search_field:
                return

            if query.search_field.value == "IS=":
                if not self.ISSN_VALUE_REGEX.match(
                    query.value
                ) and not self.ISBN_VALUE_REGEX.match(query.value):
                    self.add_linter_message(
                        QueryErrorCode.ISBN_FORMAT_INVALID,
                        positions=[query.position or (-1, -1)],
                    )

            return

        # Recursively call the function on the child querys
        for child in query.children:
            self.check_issn_isbn_format(child)

    def check_doi_format(self, query: "Query") -> None:
        """Check for the correct format of DOI."""

        if query.is_term():
            if not query.search_field:
                return

            if query.search_field.value == "DO=":
                if not self.DOI_VALUE_REGEX.match(query.value):
                    self.add_linter_message(
                        QueryErrorCode.DOI_FORMAT_INVALID,
                        positions=[query.position or (-1, -1)],
                    )
            return

        # Recursively call the function on the child querys
        for child in query.children:
            self.check_doi_format(child)

    def get_nr_terms_all(self, query: Query) -> int:
        """Get the number of terms in the query."""

        if query.is_term():
            if query.search_field and query.search_field.value == "ALL=":
                return 1

            return 0

        # Count the number of terms in the query
        nr_terms = 0
        for child in query.children:
            nr_terms += self.get_nr_terms_all(child)

        return nr_terms

    def check_nr_search_terms(self, query: Query) -> None:
        """Check the number of search terms in the query."""
        nr_terms = query.get_nr_leaves()
        if nr_terms > 1600:
            self.add_linter_message(
                QueryErrorCode.TOO_MANY_SEARCH_TERMS,
                positions=[query.position or (-1, -1)],
                details="The maximum number of search terms is 16,000.",
            )
        nr_all_terms = self.get_nr_terms_all(query)
        if nr_all_terms > 50:
            self.add_linter_message(
                QueryErrorCode.TOO_MANY_SEARCH_TERMS,
                positions=[query.position or (-1, -1)],
                details="The maximum number of search terms (for ALL Fields) is 50.",
            )

    def validate_query_tree(self, query: "Query") -> None:
        """
        Validate the query tree.
        This method is called after the query tree has been built.
        """

        self.check_year_without_search_terms(query)

        self.check_wildcards(query)
        self.check_unsupported_wildcards(query)
        self.check_unsupported_search_fields_in_query(query)
        self.check_unbalanced_quotes_in_terms(query)

        term_field_query = self.get_query_with_fields_at_terms(query)
        self.check_year_format(term_field_query)
        self.check_nr_search_terms(term_field_query)
        self.check_issn_isbn_format(term_field_query)
        self.check_doi_format(term_field_query)
        self._check_date_filters_in_subquery(term_field_query)
        self._check_journal_filters_in_subquery(term_field_query)
        self._check_redundant_terms(term_field_query)


class WOSQueryListLinter(QueryListLinter):
    """WOSQueryListLinter"""

    parser: "search_query.wos.parser.WOSListParser"

    def __init__(
        self,
        parser: "search_query.wos.parser.WOSListParser",
        string_parser_class: typing.Type["search_query.wos.parser.WOSParser"],
    ):
        super().__init__(
            parser=parser,
            string_parser_class=string_parser_class,
        )
        self.messages: dict = {}

    def validate_list_tokens(self) -> None:
        """Lint the list parser."""

        # try:
        #     self.tokenize_list()
        # except ValueError:  # may catch other errors here
        #     self.add_linter_message(
        #         QueryErrorCode.TOKENIZING_FAILED,
        #         list_position=self.GENERAL_ERROR_POSITION,
        #         position=(-1, -1),
        #     )

        missing_root = self._check_missing_root()
        self._check_missing_operator_nodes(missing_root)
        self._check_invalid_list_reference()
        self._check_query_tokenization()
        self._validate_operator_node()

    def _check_missing_root(self) -> bool:
        missing_root = False
        root_node_content: str = str(
            list(self.parser.query_dict.values())[-1]["node_content"]
        )
        # Raise an error if the last item of the list is not the last combining string
        if "#" not in root_node_content:
            self.add_linter_message(
                QueryErrorCode.MISSING_ROOT_NODE,
                list_position=GENERAL_ERROR_POSITION,
                positions=[(-1, -1)],
            )
            missing_root = True
        return missing_root

    def _check_missing_operator_nodes(self, missing_root: bool) -> None:
        if missing_root:
            return
        # require combining list items
        if not any(
            "#" in str(query["node_content"])
            for query in self.parser.query_dict.values()
        ):
            # If there is no combining list item, raise a linter exception
            # Individual list items can not be connected
            # raise ValueError("[ERROR] No combining list item found.")
            self.add_linter_message(
                QueryErrorCode.MISSING_OPERATOR_NODES,
                list_position=GENERAL_ERROR_POSITION,
                positions=[(-1, -1)],
            )

    def _validate_operator_node(self) -> None:
        """Validate the tokens of the combining list element."""

        for node_nr, node in self.parser.query_dict.items():
            if node["type"] != ListTokenTypes.OPERATOR_NODE:
                continue

            tokens = self.parser.tokenize_operator_node(node["node_content"], node_nr)

            for token in tokens:
                if token.type == OperatorNodeTokenTypes.UNKNOWN:
                    self.add_linter_message(
                        QueryErrorCode.TOKENIZING_FAILED,
                        list_position=GENERAL_ERROR_POSITION,
                        positions=[token.position],
                    )

            # Note: details should pass "format should be #1 [operator] #2"

            # Must start with LIST_ITEM
            if tokens[0].type != OperatorNodeTokenTypes.LIST_ITEM_REFERENCE:
                details = f"First token for query item {node_nr} must be a list item."
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    list_position=GENERAL_ERROR_POSITION,
                    positions=[tokens[0].position],
                    details=details,
                )
                return

            # Expect alternating pattern after first LIST_ITEM
            expected = OperatorNodeTokenTypes.LOGIC_OPERATOR
            for _, token in enumerate(tokens[1:], start=1):
                if token.type != expected:
                    self.add_linter_message(
                        QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                        list_position=GENERAL_ERROR_POSITION,
                        positions=[token.position],
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
                    list_position=GENERAL_ERROR_POSITION,
                    positions=[tokens[-1].position],
                    details=f"Last token of query item {node_nr} must be a list item.",
                )

    def _check_invalid_list_reference(self) -> None:
        # check if all list-references exist
        for ind, query_node in enumerate(self.parser.query_dict.values()):
            if "#" in str(query_node["node_content"]):
                # check if all list references exist
                for match in re.finditer(
                    self.parser.LIST_ITEM_REFERENCE,
                    str(query_node["node_content"]),
                ):
                    reference = match.group()
                    position = match.span()
                    if reference.replace("#", "") not in self.parser.query_dict:
                        self.add_linter_message(
                            QueryErrorCode.INVALID_LIST_REFERENCE,
                            list_position=ind,
                            positions=[position],
                            details=f"List reference {reference} not found.",
                        )

    def _check_query_tokenization(self) -> None:
        for ind, query_node in enumerate(self.parser.query_dict.values()):
            if query_node["type"] != ListTokenTypes.QUERY_NODE:
                continue
            query_parser = self.string_parser_class(
                query_str=query_node["node_content"],
                search_field_general=self.parser.search_field_general,
                mode=self.parser.mode,
            )
            try:
                query_parser.parse()
            except ValueError:
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED,
                    list_position=ind,
                    positions=[(-1, -1)],
                )
            for msg in query_parser.linter.messages:  # type: ignore
                if ind not in self.messages:
                    self.messages[ind] = []
                self.messages[ind].append(msg)
