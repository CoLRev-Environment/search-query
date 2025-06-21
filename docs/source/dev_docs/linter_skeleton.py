import typing

from search_query.constants import QueryErrorCode
from search_query.constants import TokenTypes
from search_query.linter_base import QueryStringLinter

if typing.TYPE_CHECKING:
    from search_query.query import Query


class XYQueryStringLinter(QueryStringLinter):
    """Linter for XY query strings"""

    VALID_TOKEN_SEQUENCES = {
        TokenTypes.FIELD: [TokenTypes.TERM],
        TokenTypes.TERM: [
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],
        TokenTypes.LOGIC_OPERATOR: [
            TokenTypes.TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],
        # ...
    }

    def validate_tokens(
        self,
        *,
        tokens: typing.List[Token],
        query_str: str,
        field_general: str = "",
    ) -> typing.List[Token]:
        """Main validation routine"""

        self.tokens = tokens
        self.query_str = query_str
        self.field_general = field_general

        self.check_unbalanced_parentheses()
        self.check_unknown_token_types()
        self.check_invalid_token_sequences()
        self.check_operator_capitalization()

        # custom validation

        return self.tokens

    def check_invalid_token_sequences(self) -> None:
        for i, token in enumerate(self.parser.tokens[:-1]):
            expected = self.VALID_TOKEN_SEQUENCES.get(token.type, [])
            if self.parser.tokens[i + 1].type not in expected:
                self.add_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    position=self.parser.tokens[i + 1].position,
                    details=f"Unexpected token after {token.type}",
                    fatal=True,
                )

    def validate_query_tree(self, query: Query) -> None:
        """
        Validate the query tree.
        This method is called after the query tree has been built.
        """

        self.check_quoted_terms_query(query)
        self.check_operator_capitalization_query(query)
        self.check_invalid_characters_in_term_query(query, "@&%$^~\\<>{}()[]#")
        self.check_unsupported_fields_in_query(query)
        # term_field_query = self.get_query_with_fields_at_terms(query)
