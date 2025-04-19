#!/usr/bin/env python3
"""XY query parser."""
from search_query.linter_base import QueryStringLinter


class XYQueryStringLinter(QueryStringLinter):
    """Linter for XY Query Strings"""

    def validate_tokens(self) -> None:
        """Validate token list"""

        self.check_missing_tokens()
        self.check_unknown_token_types()
        self.check_invalid_token_sequences()
        self.check_unbalanced_parentheses()
        self.add_artificial_parentheses_for_operator_precedence()
        self.check_operator_capitalization()
        self.check_invalid_characters_in_search_term("@&%$^~\\<>{}()[]#")

        # several checks are available via QueryStringLinter
