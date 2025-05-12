from search_query.constants import QueryErrorCode
from search_query.constants import TokenTypes
from search_query.linter_base import QueryStringLinter


class XYQueryStringLinter(QueryStringLinter):
    """Linter for XY query strings"""

    VALID_TOKEN_SEQUENCES = {
        TokenTypes.FIELD: [TokenTypes.SEARCH_TERM],
        TokenTypes.SEARCH_TERM: [
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.LOGIC_OPERATOR: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        # ...
    }

    def validate_tokens(self) -> None:
        """Main validation routine"""
        self.check_unbalanced_parentheses()
        self.check_unknown_token_types()
        self.check_invalid_token_sequences()
        self.check_operator_capitalization()
        self.check_invalid_characters_in_search_term("@&%$^~\\<>{}()[]#")

        # custom validation
        self.check_unsupported_search_fields()
        self.check_field_positioning()

    def check_unsupported_search_fields(self) -> None:
        for token in self.parser.tokens:
            if token.type == TokenTypes.FIELD and token.value not in VALID_FIELDS:
                self.add_linter_message(
                    QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
                    position=token.position,
                    details=f"Field {token.value} is not supported",
                )

    def check_invalid_token_sequences(self) -> None:
        for i, token in enumerate(self.parser.tokens[:-1]):
            expected = self.VALID_TOKEN_SEQUENCES.get(token.type, [])
            if self.parser.tokens[i + 1].type not in expected:
                self.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    position=self.parser.tokens[i + 1].position,
                    details=f"Unexpected token after {token.type}",
                )
