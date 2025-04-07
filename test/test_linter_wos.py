"""Web-of-Science linter unit tests."""
import unittest

from search_query.linter_wos import QueryLinter
from search_query.parser_wos import WOSParser
from search_query.query import SearchField

# ruff: noqa: E501
# flake8: noqa: E501


class TestQueryLinter(unittest.TestCase):
    """Test suite for the QueryLinter class."""

    def setUp(self) -> None:
        self.linter_messages: list = []

    def test_no_parentheses(self) -> None:
        """
        Test that the QueryLinter correctly identifies a query with no unmatched parentheses.

        This test initializes a QueryLinter instance with a test query and checks that
        the `check_unmatched_parentheses` method returns False, indicating no unmatched
        parentheses are present. It also verifies that no linter messages are generated.

        Assertions:
            - The `check_unmatched_parentheses` method should return False.
            - The length of `self.linter_messages` should be 0.
        """
        parser = WOSParser("test query")
        linter = QueryLinter(parser)
        linter.check_unmatched_parentheses()
        self.assertEqual(len(parser.linter_messages), 0)

    def test_matched_parentheses(self) -> None:
        """
        Test case for checking matched parentheses in a query string.

        This test initializes a QueryLinter object with
        a query string containing matched parentheses
        and verifies that the linter does not detect any unmatched parentheses. It also checks that
        no linter messages are generated.

        Assertions:
            - The linter should not detect any unmatched parentheses.
            - The length of linter messages should be 0.
        """
        parser = WOSParser("(test query)")
        linter = QueryLinter(parser)
        linter.check_unmatched_parentheses()
        self.assertEqual(len(parser.linter_messages), 0)

    def test_unmatched_opening_parenthesis(self) -> None:
        """
        Test case for detecting an unmatched opening parenthesis in a query.

        This test initializes a QueryLinter instance with a query containing an unmatched
        opening parenthesis and checks if the linter correctly identifies the issue.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the unmatched parenthesis.

        Asserts:
            - The linter detects unmatched parentheses.
            - The length of linter messages is 1.
            - The rule in the linter message is "F0002".
            - The message in the linter message is "Unmatched opening parenthesis '('."
            - The position in the linter message is (0, 1).
        """
        parser = WOSParser("(test query")
        linter = QueryLinter(parser)
        linter.check_unmatched_parentheses()
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F0004",
                "is_fatal": True,
                "label": "unmatched-opening-parenthesis",
                "message": "Unmatched opening parenthesis",
                "pos": (0, 1),
            },
        )

    def test_unmatched_closing_parenthesis(self) -> None:
        """
        Test case for detecting an unmatched closing parenthesis in a query string.

        This test initializes a QueryLinter object with a query string containing
        an unmatched closing parenthesis and checks if the linter correctly identifies
        the unmatched parenthesis. It verifies that the linter messages contain the
        appropriate rule, message, and position for the unmatched parenthesis.

        Assertions:
            - The linter should detect the unmatched closing parenthesis.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0002".
            - The message in the linter message should indicate an unmatched closing parenthesis.
            - The position in the linter message should be (10, 11).
        """
        parser = WOSParser("test query)")
        linter = QueryLinter(parser)
        linter.check_unmatched_parentheses()
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F0005",
                "is_fatal": True,
                "label": "unmatched-closing-parenthesis",
                "message": "Unmatched closing parenthesis",
                "pos": (10, 11),
            },
        )

    def test_multiple_unmatched_parentheses(self) -> None:
        """
        Test case for checking unmatched parentheses in a query string.

        This test verifies that the QueryLinter correctly identifies and reports
        an unmatched closing parenthesis in the query string. It checks that:
        - The linter detects the unmatched parenthesis.
        - The linter messages list contains exactly one message.
        - The message rule is "F0002".
        - The message text indicates an unmatched closing parenthesis.
        - The position of the unmatched parenthesis is correctly reported.
        """
        parser = WOSParser("(test query))")
        linter = QueryLinter(parser)
        linter.check_unmatched_parentheses()
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F0005",
                "is_fatal": True,
                "label": "unmatched-closing-parenthesis",
                "message": "Unmatched closing parenthesis",
                "pos": (12, 13),
            },
        )

    def test_nested_unmatched_parentheses(self) -> None:
        """
        Test case for checking unmatched parentheses in a nested query.

        This test initializes a QueryLinter instance with a query containing
        unmatched parentheses and verifies that the linter correctly identifies
        the unmatched opening parenthesis. It checks that the linter messages
        contain the appropriate rule, message, and position for the unmatched
        parenthesis.

        Assertions:
            - The linter's check_unmatched_parentheses method returns True.
            - The length of linter_messages is 1.
            - The rule in the first linter message is "F0002".
            - The message in the first linter message is "Unmatched opening parenthesis '('."
            - The position in the first linter message is (0, 1).
        """
        parser = WOSParser("((test query)")
        linter = QueryLinter(parser)
        linter.check_unmatched_parentheses()
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F0004",
                "is_fatal": True,
                "label": "unmatched-opening-parenthesis",
                "message": "Unmatched opening parenthesis",
                "pos": (0, 1),
            },
        )

    def test_two_operators_in_a_row(self) -> None:
        """
        Test case for detecting two operators in a row in a query string.

        This test initializes a QueryLinter object with a query string containing
        two operators in a row and checks if the linter correctly identifies the issue.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the two operators.

        Assertions:
            - The linter should detect two operators in a row.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0005".
            - The message in the linter message should indicate two operators in a row.
            - The position in the linter message should be (5, 6).
        """
        tokens = [("term1", (0, 5)), ("AND", (5, 8)), ("OR", (8, 10))]

        parser = WOSParser("term1 AND OR")
        linter = QueryLinter(parser)

        linter.check_order_of_tokens(tokens, "AND", (5, 8), 1)
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1006",
                "is_fatal": True,
                "label": "invalid-token-sequence-two-operators",
                "message": "Invalid token sequence: two operators in a row.",
                "pos": (8, 10),
            },
        )

    def test_two_search_fields_in_a_row(self) -> None:
        """
        Test case for detecting two search fields in a row in a query string.

        This test initializes a QueryLinter object with a query string containing
        two search fields in a row and checks if the linter correctly identifies the issue.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the two search fields.

        Assertions:
            - The linter should detect two search fields in a row.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0003".
            - The message in the linter message should indicate two search fields in a row.
            - The position in the linter message should be (5, 10).
        """
        tokens = [("term1", (0, 5)), ("au=", (5, 10)), ("ti=", (10, 15))]

        parser = WOSParser("term1 au= ti=")
        linter = QueryLinter(parser)
        linter.check_order_of_tokens(tokens, "au=", (5, 10), 1)
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1005",
                "is_fatal": True,
                "label": "invalid-token-sequence-two-search-fields",
                "message": "Invalid token sequence: two search fields in a row.",
                "pos": (10, 15),
            },
        )

    def test_missing_operator_between_term_and_parenthesis(self) -> None:
        """
        Test case for detecting missing operator between term and parenthesis in a query string.

        This test initializes a QueryLinter object with a query string containing
        a term followed by an opening parenthesis without an operator in between.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the missing operator.

        Assertions:
            - The linter should detect the missing operator between term and parenthesis.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0003".
            - The message in the linter message should indicate
                a missing operator between term and parenthesis.
            - The position in the linter message should be (5, 6).
        """
        parser = WOSParser("term1 (query)")
        linter = QueryLinter(parser)
        tokens = [("term1", (0, 5)), ("(", (5, 6))]
        linter.check_order_of_tokens(tokens, "term1", (0, 5), 0)
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1009",
                "is_fatal": True,
                "label": "invalid-token-sequence-missing-operator",
                "message": "Invalid token sequence: missing operator.",
                "pos": (0, 5),
            },
        )

    def test_missing_operator_between_parentheses(self) -> None:
        """
        Test case for detecting missing operator between
        closing and opening parenthesis in a query string.

        This test initializes a QueryLinter object with a query string containing
        a closing parenthesis followed by an opening parenthesis without an operator in between.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the missing operator.

        Assertions:
            - The linter should detect the missing operator between closing and opening parenthesis.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0003".
            - The message in the linter message should indicate
                a missing operator between closing and opening parenthesis.
            - The position in the linter message should be (5, 6).
        """
        parser = WOSParser(") (query)")
        linter = QueryLinter(parser)
        tokens = [(")", (0, 5)), ("(", (5, 6))]
        linter.check_order_of_tokens(tokens, ")", (0, 5), 0)
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1009",
                "is_fatal": True,
                "label": "invalid-token-sequence-missing-operator",
                "message": "Invalid token sequence: missing operator.",
                "pos": (0, 5),
            },
        )

    def test_missing_operator_between_term_and_search_field(self) -> None:
        """
        Test case for detecting missing operator between term and search field in a query string.

        This test initializes a QueryLinter object with a query string containing
        a term followed by a search field without an operator in between.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the missing operator.

        Assertions:
            - The linter should detect the missing operator between term and search field.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0003".
            - The message in the linter message should
                indicate a missing operator between term and search field.
            - The position in the linter message should be (5, 10).
        """
        tokens = [("term1", (0, 5)), ("au=", (5, 8))]
        parser = WOSParser("term1 au=")
        linter = QueryLinter(parser)
        linter.check_order_of_tokens(tokens, "term1", (0, 5), 0)
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1009",
                "is_fatal": True,
                "label": "invalid-token-sequence-missing-operator",
                "message": "Invalid token sequence: missing operator.",
                "pos": (0, 5),
            },
        )

    def test_near_distance_within_range(self) -> None:
        """
        Test case for NEAR operator with a specified distance within the allowed range.

        This test initializes a QueryLinter object with a query string containing
        the NEAR operator with a distance within the allowed range (<= 15).
        It verifies that the linter does not detect any issues with the NEAR distance.

        Assertions:
            - The linter should not detect any NEAR distance out of range.
            - The linter messages list should be empty.
        """
        parser = WOSParser("term1 NEAR/10 term2")
        linter = QueryLinter(parser)
        tokens = [("term1", (0, 5)), ("NEAR/10", (5, 12))]
        linter.check_near_distance_in_range(tokens, 1)
        self.assertEqual(len(parser.linter_messages), 0)

    def test_near_distance_out_of_range(self) -> None:
        """
        Test case for NEAR operator with a specified distance out of the allowed range.

        This test initializes a QueryLinter object with a query string containing
        the NEAR operator with a distance out of the allowed range (> 15).
        It verifies that the linter correctly identifies the NEAR distance out of range.

        Assertions:
            - The linter should detect the NEAR distance out of range.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0006".
            - The message in the linter message should indicate NEAR operator distance out of range.
            - The position in the linter message should be (5, 13).
        """
        parser = WOSParser("term1 NEAR/20 term2")
        linter = QueryLinter(parser)
        tokens = [("term1", (0, 5)), ("NEAR/20", (5, 13))]
        linter.check_near_distance_in_range(tokens, 1)
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1007",
                "is_fatal": True,
                "label": "near-distance-too-large",
                "message": "NEAR distance is too large (max: 15).",
                "pos": (5, 13),
            },
        )

    def test_near_without_distance(self) -> None:
        """
        Test case for NEAR operator without a specified distance.

        This test initializes a QueryLinter object with a query string containing
        the NEAR operator without a specified distance.
        It verifies that the linter does not detect any issues with the NEAR operator.

        Assertions:
            - The linter should not detect any NEAR distance out of range.
            - The linter messages list should be empty.
        """
        parser = WOSParser("term1 NEAR term2")
        linter = QueryLinter(parser)
        tokens = [("term1", (0, 5)), ("NEAR", (5, 9))]
        linter.check_near_distance_in_range(tokens, 1)
        self.assertEqual(len(parser.linter_messages), 0)

    def test_no_unsupported_wildcards(self) -> None:
        """
        Test case for a query string with no unsupported wildcards.

        This test initializes a QueryLinter object with a query string containing
        no unsupported wildcards and verifies that the linter does not detect any issues.

        Assertions:
            - The linter should not detect any unsupported wildcards.
            - The linter messages list should be empty.
        """
        parser = WOSParser("term1 term2")
        linter = QueryLinter(parser)
        linter.check_unsupported_wildcards("term1 term2")
        self.assertEqual(len(parser.linter_messages), 0)

    def test_unsupported_wildcards(self) -> None:
        """
        Test case for a query string with unsupported wildcards.

        This test initializes a QueryLinter object with a query string containing
        unsupported wildcards and verifies that the linter correctly identifies the issue.

        Assertions:
            - The linter should detect unsupported wildcards.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F1001".
            - The message in the linter message should indicate unsupported wildcards.
            - The position in the linter message should be (5, 6).
        """
        parser = WOSParser("term1 !term2")
        linter = QueryLinter(parser)
        linter.check_unsupported_wildcards("term1 !term2")
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1002",
                "label": "unsupported-wildcard",
                "message": "Unsupported wildcard in search string.",
                "is_fatal": True,
                "pos": (6, 7),
            },
        )

    def test_standalone_wildcard(self) -> None:
        """
        Test case for a query string with a standalone wildcard.

        This test initializes a QueryLinter object with a query string containing
        a standalone wildcard and verifies that the linter correctly identifies the issue.

        Assertions:
            - The linter should detect the standalone wildcard.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F1002".
            - The message in the linter message should indicate a standalone wildcard.
            - The position in the linter message should be (5, 6).
        """
        parser = WOSParser('term1 "?" term2')
        linter = QueryLinter(parser)
        linter.check_unsupported_wildcards('term1 "?" term2')
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1008",
                "is_fatal": True,
                "label": "wildcard-standalone",
                "message": "Wildcard cannot be standalone.",
                "pos": (7, 8),
            },
        )

    def test_wildcard_within_term(self) -> None:
        """
        Test case for a query string with a wildcard within a term.

        This test initializes a QueryLinter object with a query string containing
        a wildcard within a term and verifies that the linter does not detect any issues.

        Assertions:
            - The linter should not detect any unsupported wildcards.
            - The linter messages list should be empty.
        """
        parser = WOSParser("term1 te?m2")
        linter = QueryLinter(parser)
        linter.check_unsupported_wildcards("term1 te?m2")
        self.assertEqual(len(parser.linter_messages), 0)

    def test_no_unsupported_right_hand_wildcards(self) -> None:
        """
        Test case for a query string with no unsupported right-hand wildcards.

        This test initializes a QueryLinter object with a query string containing
        no unsupported right-hand wildcards and verifies that the linter does not detect any issues.

        Assertions:
            - The linter should not detect any unsupported right-hand wildcards.
            - The linter messages list should be empty.
        """
        parser = WOSParser("term1 term2*")
        linter = QueryLinter(parser)
        linter.check_unsupported_right_hand_wildcards("term2*", 5, (6, 7))
        self.assertEqual(len(parser.linter_messages), 0)

    def test_unsupported_right_hand_wildcard_after_special_character(self) -> None:
        """
        Test case for a query string with an unsupported
        right-hand wildcard after a special character.

        This test initializes a QueryLinter object with a query string containing
        an unsupported right-hand wildcard after a special character and verifies that the linter
        correctly identifies the issue.

        Assertions:
            - The linter should detect the unsupported right-hand wildcard.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F1001".
            - The message in the linter message should
                indicate unsupported wildcard after a special character.
            - The position in the linter message should be (5, 6).
        """
        parser = WOSParser("term1 term2!*")
        linter = QueryLinter(parser)
        linter.check_unsupported_right_hand_wildcards("term2!*", 6, (6, 7))
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1004",
                "is_fatal": True,
                "label": "wildcard-after-special-char",
                "message": "Wildcard cannot be preceded by special characters.",
                "pos": (6, 7),
            },
        )

    def test_unsupported_right_hand_wildcard_with_less_than_three_characters(
        self,
    ) -> None:
        """
        Test case for a query string with an unsupported
        right-hand wildcard preceded by less than three characters.

        This test initializes a QueryLinter object with a query string containing
        an unsupported right-hand wildcard preceded by less than
        three characters and verifies that the linter
        correctly identifies the issue.

        Assertions:
            - The linter should detect the unsupported right-hand wildcard.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F1001".
            - The message in the linter message should indicate
                right-hand wildcard must be preceded by at least three characters.
            - The position in the linter message should be (0, 2).
        """
        parser = WOSParser("te*")
        linter = QueryLinter(parser)
        linter.check_unsupported_right_hand_wildcards("te*", 2, (0, 2))
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1003",
                "is_fatal": True,
                "label": "wildcard-short-length",
                "message": "Right-hand wildcard must preceded by at least three characters.",
                "pos": (0, 2),
            },
        )

    def test_no_left_hand_wildcard(self) -> None:
        """
        Test case for a query string with no left-hand wildcard.

        This test initializes a QueryLinter object with a query string containing
        no left-hand wildcard and verifies that the linter does not detect any issues.

        Assertions:
            - The linter should not detect any wrong left-hand wildcard usage.
            - The linter messages list should be empty.
        """
        parser = WOSParser("term1 term2")
        linter = QueryLinter(parser)
        linter.check_format_left_hand_wildcards("term2", (6, 11))
        self.assertEqual(len(parser.linter_messages), 0)

    def test_valid_left_hand_wildcard(self) -> None:
        """
        Test case for a query string with a valid left-hand wildcard.

        This test initializes a QueryLinter object with a query string containing
        a valid left-hand wildcard and verifies that the linter does not detect any issues.

        Assertions:
            - The linter should not detect any wrong left-hand wildcard usage.
            - The linter messages list should be empty.
        """
        parser = WOSParser("term1 *term2")
        linter = QueryLinter(parser)
        linter.check_format_left_hand_wildcards("*term2", (6, 12))
        self.assertEqual(len(parser.linter_messages), 0)

    def test_invalid_left_hand_wildcard(self) -> None:
        """
        Test case for a query string with an invalid left-hand wildcard.

        This test initializes a QueryLinter object with a query string containing
        an invalid left-hand wildcard and verifies that the linter correctly identifies the issue.

        Assertions:
            - The linter should detect the wrong left-hand wildcard usage.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F1001".
            - The message in the linter message should indicate
                left-hand wildcard must be followed by at least three characters.
            - The position in the linter message should be (0, 2).
        """
        parser = WOSParser("*te")
        linter = QueryLinter(parser)
        linter.check_format_left_hand_wildcards("*te", (0, 2))
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1010",
                "is_fatal": True,
                "label": "wildcard-left-short-length",
                "message": "Left-hand wildcard must be preceded by at least three characters.",
                "pos": (0, 2),
            },
        )

    def test_valid_issn_format(self) -> None:
        """
        Test case for a query string with a valid ISSN format.

        This test initializes a QueryLinter object with a query string containing
        a valid ISSN and verifies that the linter does not detect any issues.

        Assertions:
            - The linter should not detect any ISSN format issues.
            - The linter messages list should be empty.
        """
        parser = WOSParser("1234-5678")
        linter = QueryLinter(parser)
        linter.check_issn_isbn_format(
            "1234-5678", SearchField(value="is=", position=(0, 3))
        )
        self.assertEqual(len(parser.linter_messages), 0)

    def test_invalid_issn_format(self) -> None:
        """
        Test case for a query string with an invalid ISSN format.

        This test initializes a QueryLinter object with a query string containing
        an invalid ISSN and verifies that the linter correctly identifies the issue.

        Assertions:
            - The linter should detect the ISSN format issue.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0008".
            - The message in the linter message should indicate ISSN/ISBN format is incorrect.
            - The position in the linter message should be (0, 3).
        """
        parser = WOSParser("1234-567")
        linter = QueryLinter(parser)
        linter.check_issn_isbn_format(
            "1234-567", SearchField(value="is=", position=(0, 3))
        )
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1011",
                "is_fatal": True,
                "label": "isbn-format-invalid",
                "message": "Invalid ISBN format.",
                "pos": (0, 3),
            },
        )

    def test_valid_isbn_format(self) -> None:
        """
        Test case for a query string with a valid ISBN format.

        This test initializes a QueryLinter object with a query string containing
        a valid ISBN and verifies that the linter does not detect any issues.

        Assertions:
            - The linter should not detect any ISBN format issues.
            - The linter messages list should be empty.
        """
        parser = WOSParser("978-3-16-148410-0")
        linter = QueryLinter(parser)
        linter.check_issn_isbn_format(
            "978-3-16-148410-0", SearchField(value="is=", position=(0, 3))
        )
        self.assertEqual(len(parser.linter_messages), 0)

    def test_invalid_isbn_format(self) -> None:
        """
        Test case for a query string with an invalid ISBN format.

        This test initializes a QueryLinter object with a query string containing
        an invalid ISBN and verifies that the linter correctly identifies the issue.

        Assertions:
            - The linter should detect the ISBN format issue.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0008".
            - The message in the linter message should indicate ISSN/ISBN format is incorrect.
            - The position in the linter message should be (0, 3).
        """
        parser = WOSParser("978-3-16-148410")
        linter = QueryLinter(parser)
        linter.check_issn_isbn_format(
            "978-3-16-148410", SearchField(value="is=", position=(0, 3))
        )
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1011",
                "is_fatal": True,
                "label": "isbn-format-invalid",
                "message": "Invalid ISBN format.",
                "pos": (0, 3),
            },
        )

    def test_valid_doi_format(self) -> None:
        """
        Test case for a query string with a valid DOI format.

        This test initializes a QueryLinter object with a query string containing
        a valid DOI and verifies that the linter does not detect any issues.

        Assertions:
            - The linter should not detect any DOI format issues.
            - The linter messages list should be empty.
        """
        parser = WOSParser("10.1000/xyz123")
        linter = QueryLinter(parser)
        linter.check_doi_format(
            "10.1000/xyz123", SearchField(value="do=", position=(0, 3))
        )
        self.assertEqual(len(parser.linter_messages), 0)

    def test_invalid_doi_format(self) -> None:
        """
        Test case for a query string with an invalid DOI format.

        This test initializes a QueryLinter object with a query string containing
        an invalid DOI and verifies that the linter correctly identifies the issue.

        Assertions:
            - The linter should detect the DOI format issue.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0008".
            - The message in the linter message should indicate DOI format is incorrect.
            - The position in the linter message should be (0, 3).
        """
        parser = WOSParser("12.1000/xyz")
        linter = QueryLinter(parser)
        linter.check_doi_format(
            "12.1000/xyz", SearchField(value="do=", position=(0, 3))
        )
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "F1012",
                "is_fatal": True,
                "label": "doi-format-invalid",
                "message": "Invalid DOI format.",
                "pos": (0, 3),
            },
        )

    def test_handle_multiple_same_level_operators_change(self) -> None:
        """
        Test the handle_multiple_same_level_operators method of the QueryLinter class.

        This test checks if the linter correctly identifies and handles multiple operators
        at the same level in a query string. It verifies that the linter sets the
        multiple_same_level_operators attribute to True and adds the appropriate message
        to the linter_messages list.

        The test uses the following tokens:
        - ("term1", (0, 5))
        - ("AND", (5, 8))
        - ("term2", (8, 13))
        - ("OR", (13, 15))
        - ("term3", (15, 20))

        The expected linter message is:
        - rule: "F0007"
        - message: "The operator changed at the same level. Please introduce parentheses."
        - position: (13, 15)
        """

        tokens = [
            ("term1", (0, 5)),
            ("AND", (5, 8)),
            ("term2", (8, 13)),
            ("OR", (13, 15)),
            ("term3", (15, 20)),
        ]
        parser = WOSParser("term1 AND term2 OR term3")
        linter = QueryLinter(parser)
        linter.handle_multiple_same_level_operators(tokens, 0)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "W1003",
                "is_fatal": False,
                "label": "operator-changed-at-same-level",
                "message": "Operator changed at the same level (currently relying on implicit operator precedence, explicit parentheses are recommended)",
                "pos": (13, 15),
            },
        )

    def test_handle_multiple_same_level_operators_issue(self) -> None:
        """
        Test case for handle_multiple_same_level_operators with issues.

        This test initializes a QueryLinter object with a query string containing
        multiple operators at the same level with issues. It verifies that the linter
        correctly identifies the issue with the operators.

        Assertions:
            - The linter should detect issues with the operators.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "F0007".
            - The message in the linter message should indicate operator change at the same level.
            - The position in the linter message should be (13, 17).
        """
        tokens = [
            ("term1", (0, 5)),
            ("AND", (5, 8)),
            ("term2", (8, 13)),
            ("NEAR", (13, 17)),
            ("term3", (17, 22)),
        ]
        parser = WOSParser("term1 AND term2 NEAR term3")
        linter = QueryLinter(parser)
        linter.handle_multiple_same_level_operators(tokens, 0)
        self.assertEqual(len(parser.linter_messages), 1)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "W1003",
                "is_fatal": False,
                "label": "operator-changed-at-same-level",
                "message": "Operator changed at the same level (currently relying on implicit operator precedence, explicit parentheses are recommended)",
                "pos": (13, 17),
            },
        )

    def test_handle_multiple_same_level_operators_nested_no_issue(self) -> None:
        """
        Test case for handling multiple same level operators
        within nested parentheses without any issues.

        This test verifies that the QueryLinter correctly
        handles a query with multiple same level operators
        (AND, OR) nested within parentheses and does not flag any issues.

        Steps:
        1. Define a list of tokens representing the query "term1 AND (term2 OR term3)".
        2. Initialize the QueryLinter with the query and an empty list for linter messages.
        3. Call the handle_multiple_same_level_operators method on the linter instance.
        4. Assert that the linter does not flag multiple same level operators.
        5. Assert that no linter messages are generated.

        Assertions:
        - linter.multiple_same_level_operators should be False.
        - len(self.linter_messages) should be 0.
        """

        tokens = [
            ("term1", (0, 5)),
            ("AND", (5, 8)),
            ("(", (8, 9)),
            ("term2", (9, 14)),
            ("OR", (14, 16)),
            ("term3", (16, 21)),
            (")", (21, 22)),
        ]
        parser = WOSParser("term1 AND (term2 OR term3)")
        linter = QueryLinter(parser)
        linter.handle_multiple_same_level_operators(tokens, 0)
        self.assertEqual(len(parser.linter_messages), 0)

    def test_handle_multiple_same_level_operators_with_near(self) -> None:
        """
        Test the handling of multiple same-level operators with the 'NEAR' operator.

        This test checks if the QueryLinter correctly identifies and handles the
        presence of multiple same-level operators, specifically when 'NEAR' and 'AND'
        operators are used in the query. It verifies that the linter sets the
        `multiple_same_level_operators` flag and adds the appropriate message to
        `linter_messages`.

        The test uses the following tokens:
        - ("term1", (0, 5))
        - ("NEAR/5", (5, 11))
        - ("term2", (11, 16))
        - ("AND", (16, 19))
        - ("term3", (19, 24))

        Assertions:
        - `linter.multiple_same_level_operators` is set to True.
        - The first message in `linter_messages` has:
          - 'rule' set to "F0007".
          - 'message' set to "The operator changed at the same level. Please introduce parentheses."
          - 'position' set to (16, 19).
        """

        tokens = [
            ("term1", (0, 5)),
            ("NEAR/5", (5, 11)),
            ("term2", (11, 16)),
            ("AND", (16, 19)),
            ("term3", (19, 24)),
        ]
        parser = WOSParser("term1 NEAR/5 term2 AND term3")
        linter = QueryLinter(parser)
        linter.handle_multiple_same_level_operators(tokens, 0)
        self.assertEqual(
            parser.linter_messages[0],
            {
                "code": "W1003",
                "is_fatal": False,
                "label": "operator-changed-at-same-level",
                "message": "Operator changed at the same level (currently relying on implicit operator precedence, explicit parentheses are recommended)",
                "pos": (16, 19),
            },
        )


if __name__ == "__main__":
    unittest.main()
