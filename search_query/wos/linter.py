#!/usr/bin/env python3
"""Web-of-Science query linter."""
from __future__ import annotations

import re
import typing

from search_query.constants import GENERAL_ERROR_POSITION
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.linter_base import QueryListLinter
from search_query.linter_base import QueryStringLinter
from search_query.query import Query
from search_query.wos.constants import syntax_str_to_generic_field_set
from search_query.wos.constants import VALID_fieldS_REGEX
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

    VALID_fieldS_REGEX = VALID_fieldS_REGEX

    PLATFORM: PLATFORM = PLATFORM.WOS

    VALID_TOKEN_SEQUENCES = {
        TokenTypes.FIELD: [
            TokenTypes.TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.TERM: [
            TokenTypes.TERM,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PROXIMITY_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.LOGIC_OPERATOR: [
            TokenTypes.TERM,
            TokenTypes.FIELD,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.PROXIMITY_OPERATOR: [
            TokenTypes.TERM,
            TokenTypes.PARENTHESIS_OPEN,
            TokenTypes.FIELD,
        ],
        TokenTypes.PARENTHESIS_OPEN: [
            TokenTypes.FIELD,
            TokenTypes.TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        TokenTypes.PARENTHESIS_CLOSED: [
            TokenTypes.PARENTHESIS_CLOSED,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PROXIMITY_OPERATOR,
        ],
    }

    def __init__(
        self,
        query_str: str = "",
        *,
        original_str: typing.Optional[str] = None,
        silent: bool = False,
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_str=query_str,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )

    def validate_tokens(
        self,
        *,
        tokens: typing.List[Token],
        query_str: str,
        field_general: str = "",
    ) -> typing.List[Token]:
        """Performs a pre-linting"""

        self.tokens = tokens
        self.query_str = query_str
        self.field_general = field_general

        self.check_invalid_syntax()
        self.check_missing_tokens()
        self.check_unknown_token_types()
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()
        if self.has_fatal_errors():
            return self.tokens

        self.check_invalid_characters_in_term(
            "@%^~\\<>{}()[]#", QueryErrorCode.WOS_INVALID_CHARACTER
        )
        # Note : "&" is allowed for journals (e.g., "Information & Management")
        # When used for search terms, it seems to be translated to "AND"
        self.check_near_distance_in_range(max_value=15)

        self.check_general_field()
        self.check_missing_fields()

        self.check_implicit_near()
        return self.tokens

    def check_invalid_syntax(self) -> None:
        """Check for invalid syntax in the query string."""

        # Check for erroneous field syntax
        match = re.search(r"\[[A-Za-z]*\]", self.query_str)
        if match:
            self.add_message(
                QueryErrorCode.INVALID_SYNTAX,
                positions=[match.span()],
                details="WOS fields must be before search terms and "
                "without brackets, e.g. AB=robot or TI=monitor. "
                f"'{match.group(0)}' is invalid.",
                fatal=True,
            )

    def syntax_str_to_generic_field_set(self, field_value: str) -> set:
        return syntax_str_to_generic_field_set(field_value)

    def check_year_without_terms(self, query: Query) -> None:
        """Check if the year is used without a search terms."""

        if query.is_term():
            if not query.field:
                return

            if not YEAR_PUBLISHED_FIELD_REGEX.match(query.field.value):
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
            self.add_message(
                QueryErrorCode.YEAR_WITHOUT_TERMS,
                positions=positions,
                fatal=True,
            )

    def check_missing_fields(
        self,
    ) -> None:
        """Check for missing search fields."""

        missing_positions = []

        first_token = self.tokens[0]
        if first_token.type not in [TokenTypes.FIELD, TokenTypes.PARENTHESIS_OPEN]:
            missing_positions.append(first_token.position)

        previous_token = self.tokens[0].type

        # iterate over remaining tokens on the first level
        level = 0
        for token in self.tokens[1:]:
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                level += 1
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                level -= 1
            elif (
                level == 0
                and token.type == TokenTypes.TERM
                and previous_token != TokenTypes.FIELD
            ):
                missing_positions.append(token.position)
            previous_token = token.type

        if missing_positions:
            self.add_message(
                QueryErrorCode.FIELD_MISSING,
                positions=missing_positions,
            )

    def check_implicit_near(self) -> None:
        """Check for implicit NEAR operator."""
        for token in self.tokens:
            if token.value == "NEAR":
                self.add_message(
                    QueryErrorCode.IMPLICIT_NEAR_VALUE,
                    positions=[token.position],
                )
                token.value = "NEAR/15"

    def check_year_format(self, query: Query) -> None:
        """Check for the correct format of year."""

        if query.is_term():
            if not query.field:
                return
            if not YEAR_PUBLISHED_FIELD_REGEX.match(query.field.value):
                return
            if any(char in query.value for char in ["*", "?", "$"]):
                self.add_message(
                    QueryErrorCode.WILDCARD_IN_YEAR,
                    positions=[query.position] if query.position else [],
                    fatal=True,
                )
                return

            if not self.YEAR_VALUE_REGEX.match(query.value):
                self.add_message(
                    QueryErrorCode.YEAR_FORMAT_INVALID,
                    positions=[query.position] if query.position else [],
                    fatal=True,
                )
                return

            # Check if the yearspan is not more than 5 years
            if len(query.value) > 4:
                if int(query.value[5:9]) - int(query.value[0:4]) > 5:
                    # Change the year span to five years
                    query.value = (
                        str(int(query.value[5:9]) - 5) + "-" + query.value[5:9]
                    )

                    self.add_message(
                        QueryErrorCode.YEAR_SPAN_VIOLATION,
                        positions=[query.position] if query.position else [],
                        fatal=True,
                    )

        for child in query.children:
            self.check_year_format(child)

    def check_invalid_token_sequences(self) -> None:
        """Check for the correct order of tokens in the query."""

        # Check the first token
        if self.tokens[0].type not in [
            TokenTypes.TERM,
            TokenTypes.FIELD,
            TokenTypes.PARENTHESIS_OPEN,
        ]:
            self.add_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                positions=[self.tokens[0].position],
                details=f"Cannot start with {self.tokens[0].type.value}",
                fatal=True,
            )

        tokens = self.tokens
        for index in range(len(tokens) - 1):
            token = tokens[index]
            next_token = tokens[index + 1]

            # # Skip known exceptions like NEAR proximity modifier (custom rule)
            # if (
            #     token.type == TokenTypes.TERM
            #     and next_token.value == "("
            #     and index > 0
            #     and tokens[index - 1].value.upper() == "NEAR"
            # ):
            #     continue

            # # Allow known languages after parenthesis (custom rule)
            # if token.value == ")" and YEAR_PUBLISHED_FIELD_REGEX.match(
            #     next_token.value
            # ):
            #     continue

            # Two operators in a row
            if token.is_operator() and next_token.is_operator():
                self.add_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    positions=[(token.position[0], next_token.position[1])],
                    details="Two operators in a row are not allowed.",
                    fatal=True,
                )
                continue

            # Two search fields in a row
            if token.type == TokenTypes.FIELD and next_token.type == TokenTypes.FIELD:
                self.add_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    positions=[(token.position[0], next_token.position[1])],
                    fatal=True,
                )
                continue

            # Check transition
            allowed_next_types = self.VALID_TOKEN_SEQUENCES.get(token.type, [])
            if next_token.type not in allowed_next_types:
                self.add_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    positions=[(token.position[0], next_token.position[1])],
                    fatal=True,
                )

        # Check the last token
        if self.tokens[-1].type in [
            TokenTypes.PARENTHESIS_OPEN,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.FIELD,
        ]:
            self.add_message(
                QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                positions=[self.tokens[-1].position],
                details=f"Cannot end with {self.tokens[-1].type.value}",
                fatal=True,
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
                self.add_message(
                    QueryErrorCode.WOS_WILDCARD_UNSUPPORTED,
                    positions=[position],
                    details="The '!' character is not supported in WOS search strings.",
                    fatal=True,
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
                        self.add_message(
                            QueryErrorCode.WILDCARD_STANDALONE,
                            positions=[query.position] if query.position else [],
                            details=(
                                f"Wildcard '{charachter}' "
                                "cannot be used as a standalone character."
                            ),
                            fatal=True,
                        )

                    elif len(value) == index + 1:
                        # Right-hand wildcard
                        self.check_unsupported_right_hand_wildcards(
                            query=query, index=index
                        )

                    elif index == 0 and len(value) > 1:
                        # Left-hand wildcard
                        self.check_format_left_hand_wildcards(query)

        for child in query.children:
            self.check_wildcards(child)

    def check_unsupported_right_hand_wildcards(self, query: Query, index: int) -> None:
        """Check for unsupported right-hand wildcards in the search string."""

        if query.value[index - 1] in ["/", "@", "#", ".", ":", ";", "!"]:
            self.add_message(
                QueryErrorCode.WILDCARD_AFTER_SPECIAL_CHAR,
                positions=[query.position] if query.position else [],
                details=(
                    f"Wildcard '{query.value[index]}' "
                    "is not allowed after a special character."
                ),
                fatal=True,
            )

        if len(query.value) < 4:
            self.add_message(
                QueryErrorCode.WILDCARD_RIGHT_SHORT_LENGTH,
                positions=[query.position] if query.position else [],
                fatal=True,
            )

    def check_format_left_hand_wildcards(self, query: Query) -> None:
        """Check for wrong usage among left-hand wildcards in the search string."""

        if len(query.value) < 4:
            self.add_message(
                QueryErrorCode.WILDCARD_LEFT_SHORT_LENGTH,
                positions=[query.position] if query.position else [],
                fatal=True,
            )

    def check_issn_isbn_format(self, query: Query) -> None:
        """Check for the correct format of ISSN and ISBN."""

        if query.is_term():
            if not query.field:
                return

            if query.field.value == "IS=":
                if not self.ISSN_VALUE_REGEX.match(
                    query.value
                ) and not self.ISBN_VALUE_REGEX.match(query.value):
                    self.add_message(
                        QueryErrorCode.ISBN_FORMAT_INVALID,
                        positions=[query.position] if query.position else [],
                        fatal=True,
                    )

            return

        # Recursively call the function on the child queries
        for child in query.children:
            self.check_issn_isbn_format(child)

    def check_deprecated_field_tags(self, query: Query) -> None:
        """Check for deprecated field tags."""

        if query.is_term():
            if not query.field:
                return

            # TODO: clarify advice... + context (called via CI / with filename?)

            # use of the following field tags in the search interface prints
            # Search Error: Invalid field tag.
            if query.field.value in [
                "FN=",
                "VR=",
                "PT=",
                "AF=",
                "BA=",
                "BF=",
                "CA=",
                "BE=",
                "BS=",
                "CL=",
                "SP=",
                "HO=",
                "DE=",
                "ID=",
                "C1=",
                "RP=",
                "EM=",
                "RI=",
                "OI=",
                "FU=",
                "CR=",
                "NR=",
                "TC=",
                "Z9=",
                "U1=",
                "U2=",
                "PI=",
                "PU=",
                "SN=",
                "EI=",
                "BN=",
                "J9=",
                "JI=",
                "PD=",
                "SI=",
                "PN=",
                "MA=",
                "BP=",
                "EP=",
                "AR=",
            ]:
                self.add_message(
                    QueryErrorCode.LINT_DEPRECATED_SYNTAX,
                    positions=[query.field.position] if query.field.position else [],
                    fatal=True,
                    details=f"The '{query.field.value}' field is deprecated.",
                )
            elif query.field.value == "DI=":
                self.add_message(
                    QueryErrorCode.LINT_DEPRECATED_SYNTAX,
                    positions=[query.field.position] if query.field.position else [],
                    fatal=True,
                    details="The 'DI=' field is deprecated. Use 'DO=' instead. "
                    + "Use search-query upgrade XY to upgrade the search query",
                )
            elif query.field.value in [
                "D2=",
                "EY=",
                "P2=",
                "SC=",
                "GA=",
                "HP=",
                "HC=",
                "DA=",
                "ER=",
                "EF=",
            ]:
                self.add_message(
                    QueryErrorCode.LINT_DEPRECATED_SYNTAX,
                    positions=[query.field.position] if query.field.position else [],
                    fatal=True,
                    details=f"The '{query.field.value}' field is deprecated.",
                )

            return

        # Recursively call the function on the child queries
        for child in query.children:
            self.check_deprecated_field_tags(child)

    def check_doi_format(self, query: Query) -> None:
        """Check for the correct format of DOI."""

        if query.is_term():
            if not query.field:
                return

            if query.field.value == "DO=":
                if not self.DOI_VALUE_REGEX.match(query.value):
                    self.add_message(
                        QueryErrorCode.DOI_FORMAT_INVALID,
                        positions=[query.position] if query.position else [],
                        fatal=True,
                    )
            return

        # Recursively call the function on the child queries
        for child in query.children:
            self.check_doi_format(child)

    def get_nr_terms_all(self, query: Query) -> int:
        """Get the number of terms in the query."""

        if query.is_term():
            if query.field and query.field.value == "ALL=":
                return 1

            return 0

        # Count the number of terms in the query
        nr_terms = 0
        for child in query.children:
            nr_terms += self.get_nr_terms_all(child)

        return nr_terms

    def check_nr_terms(self, query: Query) -> None:
        """Check the number of search terms in the query."""
        nr_terms = query.get_nr_leaves()
        if nr_terms > 1600:  # pragma: no cover
            self.add_message(
                QueryErrorCode.TOO_MANY_TERMS,
                positions=[query.position] if query.position else [],
                details="The maximum number of search terms is 16,000.",
                fatal=True,
            )
        nr_all_terms = self.get_nr_terms_all(query)
        if nr_all_terms > 50:
            self.add_message(
                QueryErrorCode.TOO_MANY_TERMS,
                positions=[query.position] if query.position else [],
                details="The maximum number of search terms (for ALL Fields) is 50.",
                fatal=True,
            )

    def validate_query_tree(self, query: Query) -> None:
        """
        Validate the query tree.
        This method is called after the query tree has been built.
        """

        self.check_year_without_terms(query)

        self.check_wildcards(query)
        self.check_unsupported_wildcards(query)
        self.check_unsupported_fields_in_query(query)
        self.check_unbalanced_quotes_in_terms(query)

        term_field_query = self.get_query_with_fields_at_terms(query)
        self.check_year_format(term_field_query)
        self.check_nr_terms(term_field_query)
        self.check_issn_isbn_format(term_field_query)
        self.check_doi_format(term_field_query)
        self._check_date_filters_in_subquery(term_field_query)
        self._check_journal_filters_in_subquery(term_field_query)
        self._check_redundant_terms(term_field_query)
        self._check_for_wildcard_usage(term_field_query)
        self.check_deprecated_field_tags(term_field_query)


class WOSQueryListLinter(QueryListLinter):
    """WOSQueryListLinter"""

    parser: search_query.wos.parser.WOSListParser

    def __init__(
        self,
        parser: search_query.wos.parser.WOSListParser,
        string_parser_class: typing.Type[search_query.wos.parser.WOSParser],
        original_query_str: str = "",
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            parser=parser,
            string_parser_class=string_parser_class,
            original_query_str=original_query_str,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.messages: dict = {}

    def validate_list_tokens(self) -> None:
        """Lint the list parser."""

        self._check_missing_root()
        self._check_list_query_invalid_reference()

    def _check_missing_root(self) -> None:
        root_node_content: str = str(
            list(self.parser.query_dict.values())[-1]["node_content"]
        )
        # Raise an error if the last item of the list is not the last combining string
        if "#" not in root_node_content:
            self.add_message(
                QueryErrorCode.LIST_QUERY_MISSING_ROOT_NODE,
                list_position=GENERAL_ERROR_POSITION,
                positions=[],
                details="The last item of the list must be a combining string.",
                fatal=True,
            )

    def _check_list_query_invalid_reference(self) -> None:
        # check if all list-references exist
        for ind, query_node in enumerate(self.parser.query_dict.values()):
            # check if all list references exist
            for match in re.finditer(
                self.parser.LIST_ITEM_REFERENCE,
                str(query_node["node_content"]),
            ):
                reference = match.group()
                position = match.span()
                offset = query_node["content_pos"][0]
                position = (position[0] + offset, position[1] + offset)
                if reference.replace("#", "") not in self.parser.query_dict:
                    self.add_message(
                        QueryErrorCode.LIST_QUERY_INVALID_REFERENCE,
                        list_position=ind,
                        positions=[position],
                        details=f"List reference {reference} not found.",
                        fatal=True,
                    )
