#!/usr/bin/env python3
"""Web-of-Science query linter."""
import re
import typing

from search_query.constants import GENERAL_ERROR_POSITION
from search_query.constants import LinterMode
from search_query.constants import ListTokenTypes
from search_query.constants import OperatorNodeTokenTypes
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import FatalLintingException
from search_query.linter_base import QueryListLinter
from search_query.linter_base import QueryStringLinter
from search_query.parser_wos_constants import WOSSearchFieldList

if typing.TYPE_CHECKING:
    import search_query.parser_wos


class WOSQueryStringLinter(QueryStringLinter):
    """Linter for WOS Query Strings"""

    language_list = [
        "LA=",
        "Languages",
        "la=",
        "language=",
        "la",
        "language",
        "LA",
        "LANGUAGE",
    ]
    WILDCARD_CHARS = ["?", "$", "*"]

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

    parser: "search_query.parser_wos.WOSParser"

    def __init__(self, parser: "search_query.parser_wos.WOSParser"):
        self.search_str = parser.query_str
        self.parser = parser

        super().__init__(parser=parser)

    def validate_tokens(self) -> None:
        """Performs a pre-linting"""

        self.check_missing_tokens()
        self.check_unknown_token_types()
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()
        self.check_invalid_characters_in_search_term("@&%$^~\\<>{}()[]#")

        self.check_search_fields_from_json()
        self.check_implicit_near()
        self.check_year_format()
        self.check_fields()
        self.check_year_without_search_field()
        self.check_near_distance_in_range(max_value=15)
        self.check_wildcards()
        self.check_unsupported_wildcards()

    def check_year_without_search_field(self) -> None:
        """Check if the year is used without a search field."""
        year_search_field_detected = False
        count_search_fields = 0
        for token in self.parser.tokens:
            if token.value in WOSSearchFieldList.year_published_list:
                year_search_field_detected = True

            if token.type == TokenTypes.SEARCH_TERM:
                count_search_fields += 1

        if year_search_field_detected and count_search_fields < 2:
            # Year detected without other search fields
            self.add_linter_message(
                QueryErrorCode.YEAR_WITHOUT_SEARCH_FIELD,
                position=(
                    self.parser.tokens[0].position[0],
                    self.parser.tokens[-1].position[1],
                ),
            )

    def check_search_fields_from_json(
        self,
    ) -> None:
        """Check if the search field is in the list of search fields from JSON."""

        for index, token in enumerate(self.parser.tokens):
            if token.type not in [TokenTypes.FIELD, TokenTypes.PARENTHESIS_OPEN]:
                if self.parser.search_field_general == "":
                    self.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_MISSING,
                        position=(-1, -1),
                    )
                break

            if token.type == TokenTypes.FIELD:
                if index == 0 and self.parser.search_field_general != "":
                    if token.value != self.parser.search_field_general:
                        self.add_linter_message(
                            QueryErrorCode.SEARCH_FIELD_CONTRADICTION,
                            position=token.position,
                        )
                    else:
                        # Note : in basic search, when starting the query with a field,
                        # WOS raises a syntax error.
                        self.add_linter_message(
                            QueryErrorCode.SEARCH_FIELD_REDUNDANT,
                            position=token.position,
                        )

                # break: only consider the first FIELD
                # (which may come after parentheses)
                break

    def check_fields(self) -> None:
        """Check for the correct format of fields."""
        valid_fields = set().union(*WOSSearchFieldList.search_field_dict.values())
        for token in self.parser.tokens:
            if token.type == TokenTypes.FIELD:
                if token.value not in valid_fields:
                    self.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                        position=token.position,
                        details=f"Search field {token.value} at position "
                        f"{token.position} is not supported.",
                    )

    def check_implicit_near(self) -> None:
        """Check for implicit NEAR operator."""
        for token in self.parser.tokens:
            if token.value == "NEAR":
                self.add_linter_message(
                    QueryErrorCode.IMPLICIT_NEAR_VALUE,
                    position=token.position,
                )
                token.value = "NEAR/15"

    def check_year_format(self) -> None:
        """Check for the correct format of year."""
        for index, token in enumerate(self.parser.tokens):
            if token.value in WOSSearchFieldList.year_published_list:
                year_token = self.parser.tokens[index + 1]

                if any(char in year_token.value for char in ["*", "?", "$"]):
                    self.add_linter_message(
                        QueryErrorCode.WILDCARD_IN_YEAR,
                        position=year_token.position,
                    )

                # Check if the yearspan is not more than 5 years
                if len(year_token.value) > 4:
                    if int(year_token.value[5:9]) - int(year_token.value[0:4]) > 5:
                        # Change the year span to five years
                        year_token.value = (
                            str(int(year_token.value[5:9]) - 5)
                            + "-"
                            + year_token.value[5:9]
                        )

                        self.add_linter_message(
                            QueryErrorCode.YEAR_SPAN_VIOLATION,
                            position=year_token.position,
                        )

    def check_invalid_token_sequences(self) -> None:
        """Check for the correct order of tokens in the query."""

        tokens = self.parser.tokens
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
            if token.value == ")" and next_token.value in self.language_list:
                continue

            # Two operators in a row
            if token.is_operator() and next_token.is_operator():
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    position=(token.position[0], next_token.position[1]),
                    details="Two operators in a row are not allowed.",
                )
                continue

            # Two search fields in a row
            if token.type == TokenTypes.FIELD and next_token.type == TokenTypes.FIELD:
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    position=next_token.position,
                )
                continue

            # Check transition
            allowed_next_types = self.VALID_TOKEN_SEQUENCES.get(token.type, [])
            if next_token.type not in allowed_next_types:
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    position=next_token.position,
                )

    def check_unsupported_wildcards(self) -> None:
        """Check for unsupported characters in the search string."""

        # Web of Science does not support "!"
        for match in re.finditer(r"\!+", self.search_str):
            self.add_linter_message(
                QueryErrorCode.WILDCARD_UNSUPPORTED,
                position=(match.start(), match.end()),
            )

    def check_wildcards(self) -> None:
        """Check for the usage of wildcards in the search string."""

        for token in self.parser.tokens:
            token_value = token.value.replace('"', "")

            # Implement constrains from Web of Science for Wildcards
            for index, charachter in enumerate(token_value):
                if charachter in self.WILDCARD_CHARS:
                    # Check if wildcard is left or right-handed or standalone
                    if index == 0 and len(token_value) == 1:
                        self.add_linter_message(
                            QueryErrorCode.WILDCARD_STANDALONE,
                            position=token.position,
                        )

                    elif len(token_value) == index + 1:
                        # Right-hand wildcard
                        self.check_unsupported_right_hand_wildcards(
                            token=token, index=index
                        )

                    elif index == 0 and len(token_value) > 1:
                        # Left-hand wildcard
                        self.check_format_left_hand_wildcards(token=token)

                    else:
                        # Wildcard in the middle of the term
                        if token_value[index - 1] in [
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
                                position=token.position,
                            )

    def check_unsupported_right_hand_wildcards(self, token: Token, index: int) -> None:
        """Check for unsupported right-hand wildcards in the search string."""

        if token.value[index - 1] in ["/", "@", "#", ".", ":", ";", "!"]:
            self.add_linter_message(
                QueryErrorCode.WILDCARD_AFTER_SPECIAL_CHAR,
                position=token.position,
            )

        if len(token.value) < 4:
            self.add_linter_message(
                QueryErrorCode.WILDCARD_RIGHT_SHORT_LENGTH,
                position=token.position,
            )

    def check_format_left_hand_wildcards(self, token: Token) -> None:
        """Check for wrong usage among left-hand wildcards in the search string."""

        if len(token.value) < 4:
            self.add_linter_message(
                QueryErrorCode.WILDCARD_LEFT_SHORT_LENGTH,
                position=token.position,
            )

    def check_issn_isbn_format(self, token: Token) -> None:
        """Check for the correct format of ISSN and ISBN."""
        token_vale = token.value.replace('"', "")
        if not re.match(self.parser.ISSN_REGEX, token_vale) and not re.match(
            self.parser.ISBN_REGEX, token_vale
        ):
            # Add messages to self.messages
            self.add_linter_message(
                QueryErrorCode.ISBN_FORMAT_INVALID,
                position=token.position,
            )

    def check_doi_format(self, token: Token) -> None:
        """Check for the correct format of DOI."""
        token_value = token.value.replace('"', "").upper()
        if not re.match(self.parser.DOI_REGEX, token_value):
            # Add messages to self.messages
            self.add_linter_message(
                QueryErrorCode.DOI_FORMAT_INVALID,
                position=token.position,
            )


class WOSQueryListLinter(QueryListLinter):
    """WOSQueryListLinter"""

    parser: "search_query.parser_wos.WOSListParser"

    def __init__(
        self,
        parser: "search_query.parser_wos.WOSListParser",
        string_parser_class: typing.Type["search_query.parser_wos.WOSParser"],
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

        if self.has_fatal_errors():
            print("\n[FATAL:] Fatal error detected in pre-linting")
            # Print linter messages
            if self.parser.mode != LinterMode.STRICT and not self.has_fatal_errors():
                print(
                    "\n[INFO:] The following errors have been corrected by the linter:"
                )

            for level, message_list in self.messages.items():
                print(f"\n[INFO:] Linter messages for level {level}:")
                for msg in message_list:
                    details = msg["details"] if msg["details"] else msg["message"]
                    print(
                        "[Linter:] "
                        + msg["label"]
                        + "\t"
                        + details
                        + " At position "
                        + str(msg["position"])
                    )

            # Raise an exception
            # if the linter is in strict mode
            # or if a fatal error has occurred
            if (
                self.parser.mode == LinterMode.STRICT
                or self.has_fatal_errors()
                and self.messages
            ):
                l_messages = [y for x in self.messages.values() if x for y in x if y]
                print(l_messages)
                raise FatalLintingException(
                    query_string=self.parser.query_list,
                    messages=l_messages,
                )

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
                position=(-1, -1),
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
                position=(-1, -1),
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
                        position=token.position,
                    )

            # Note: details should pass "format should be #1 [operator] #2"

            # Must start with LIST_ITEM
            if tokens[0].type != OperatorNodeTokenTypes.LIST_ITEM_REFERENCE:
                details = f"First token for query item {node_nr} must be a list item."
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    list_position=GENERAL_ERROR_POSITION,
                    position=tokens[0].position,
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
                    list_position=GENERAL_ERROR_POSITION,
                    position=tokens[-1].position,
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
                            position=position,
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
                verbosity=0,  # errors are printed by the list linter
            )
            try:
                query_parser.parse()
            except FatalLintingException:  # add more specific message?""
                self.add_linter_message(
                    QueryErrorCode.TOKENIZING_FAILED,
                    list_position=ind,
                    position=(-1, -1),
                )
            for msg in query_parser.linter.messages:  # type: ignore
                if ind not in self.messages:
                    self.messages[ind] = []
                self.messages[ind].append(msg)
