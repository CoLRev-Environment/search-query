"""Web-of-Science linter unit tests."""
import unittest
from linter_wos import QueryLinter

class TestQueryLinter(unittest.TestCase):
    """Test suite for the QueryLinter class."""

    def setUp(self):
        self.linter_messages = []

    def test_no_parentheses(self):
        """
        Test that the QueryLinter correctly identifies a query with no unmatched parentheses.

        This test initializes a QueryLinter instance with a test query and checks that
        the `check_unmatched_parentheses` method returns False, indicating no unmatched
        parentheses are present. It also verifies that no linter messages are generated.

        Assertions:
            - The `check_unmatched_parentheses` method should return False.
            - The length of `self.linter_messages` should be 0.
        """
        linter = QueryLinter("test query", self.linter_messages)
        self.assertFalse(linter.check_unmatched_parentheses())
        self.assertEqual(len(self.linter_messages), 0)

    def test_matched_parentheses(self):
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
        linter = QueryLinter("(test query)", self.linter_messages)
        self.assertFalse(linter.check_unmatched_parentheses())
        self.assertEqual(len(self.linter_messages), 0)

    def test_unmatched_opening_parenthesis(self):
        """
        Test case for detecting an unmatched opening parenthesis in a query.

        This test initializes a QueryLinter instance with a query containing an unmatched
        opening parenthesis and checks if the linter correctly identifies the issue.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the unmatched parenthesis.

        Asserts:
            - The linter detects unmatched parentheses.
            - The length of linter messages is 1.
            - The rule in the linter message is "UnmatchedParenthesis".
            - The message in the linter message is "Unmatched opening parenthesis '('."
            - The position in the linter message is (0, 1).
        """
        linter = QueryLinter("(test query", self.linter_messages)
        self.assertTrue(linter.check_unmatched_parentheses())
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "UnmatchedParenthesis")
        self.assertEqual(self.linter_messages[0]['message'], "Unmatched opening parenthesis '('.")
        self.assertEqual(self.linter_messages[0]['position'], (0, 1))

    def test_unmatched_closing_parenthesis(self):
        """
        Test case for detecting an unmatched closing parenthesis in a query string.

        This test initializes a QueryLinter object with a query string containing
        an unmatched closing parenthesis and checks if the linter correctly identifies
        the unmatched parenthesis. It verifies that the linter messages contain the
        appropriate rule, message, and position for the unmatched parenthesis.

        Assertions:
            - The linter should detect the unmatched closing parenthesis.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "UnmatchedParenthesis".
            - The message in the linter message should indicate an unmatched closing parenthesis.
            - The position in the linter message should be (10, 11).
        """
        linter = QueryLinter("test query)", self.linter_messages)
        self.assertTrue(linter.check_unmatched_parentheses())
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "UnmatchedParenthesis")
        self.assertEqual(self.linter_messages[0]['message'], "Unmatched closing parenthesis ')'.")
        self.assertEqual(self.linter_messages[0]['position'], (10, 11))

    def test_multiple_unmatched_parentheses(self):
        """
        Test case for checking unmatched parentheses in a query string.

        This test verifies that the QueryLinter correctly identifies and reports
        an unmatched closing parenthesis in the query string. It checks that:
        - The linter detects the unmatched parenthesis.
        - The linter messages list contains exactly one message.
        - The message rule is "UnmatchedParenthesis".
        - The message text indicates an unmatched closing parenthesis.
        - The position of the unmatched parenthesis is correctly reported.
        """
        linter = QueryLinter("(test query))", self.linter_messages)
        self.assertTrue(linter.check_unmatched_parentheses())
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "UnmatchedParenthesis")
        self.assertEqual(self.linter_messages[0]['message'], "Unmatched closing parenthesis ')'.")
        self.assertEqual(self.linter_messages[0]['position'], (12, 13))

    def test_nested_unmatched_parentheses(self):
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
            - The rule in the first linter message is "UnmatchedParenthesis".
            - The message in the first linter message is "Unmatched opening parenthesis '('."
            - The position in the first linter message is (0, 1).
        """
        linter = QueryLinter("((test query)", self.linter_messages)
        self.assertTrue(linter.check_unmatched_parentheses())
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "UnmatchedParenthesis")
        self.assertEqual(self.linter_messages[0]['message'], "Unmatched opening parenthesis '('.")
        self.assertEqual(self.linter_messages[0]['position'], (0, 1))

    def test_two_operators_in_a_row(self):
        """
        Test case for detecting two operators in a row in a query string.

        This test initializes a QueryLinter object with a query string containing
        two operators in a row and checks if the linter correctly identifies the issue.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the two operators.

        Assertions:
            - The linter should detect two operators in a row.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "TwoOperatorInRow".
            - The message in the linter message should indicate two operators in a row.
            - The position in the linter message should be (5, 6).
        """
        tokens = [("term1", (0, 5)), ("AND", (5, 8)), ("OR", (8, 10))]
        linter = QueryLinter("term1 AND OR", self.linter_messages)
        self.assertTrue(linter.check_order_of_tokens(tokens, "AND", (5, 8), 1))
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "TwoOperatorInRow")
        self.assertEqual(self.linter_messages[0]['message'], "Two operators in a row.")
        self.assertEqual(self.linter_messages[0]['position'], (8, 10))

    def test_two_search_fields_in_a_row(self):
        """
        Test case for detecting two search fields in a row in a query string.

        This test initializes a QueryLinter object with a query string containing
        two search fields in a row and checks if the linter correctly identifies the issue.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the two search fields.

        Assertions:
            - The linter should detect two search fields in a row.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "TwoSearchFieldsInRow".
            - The message in the linter message should indicate two search fields in a row.
            - The position in the linter message should be (5, 10).
        """
        tokens = [("term1", (0, 5)), ("au=", (5, 10)), ("ti=", (10, 15))]
        linter = QueryLinter("term1 au= ti=", self.linter_messages)
        self.assertTrue(linter.check_order_of_tokens(tokens, "au=", (5, 10), 1))
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "TwoSearchFieldsInRow")
        self.assertEqual(self.linter_messages[0]['message'], "Two Search Fields in a row.")
        self.assertEqual(self.linter_messages[0]['position'], (10, 15))

    def test_missing_operator_between_term_and_parenthesis(self):
        """
        Test case for detecting missing operator between term and parenthesis in a query string.

        This test initializes a QueryLinter object with a query string containing
        a term followed by an opening parenthesis without an operator in between.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the missing operator.

        Assertions:
            - The linter should detect the missing operator between term and parenthesis.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "ParenthesisAfterTerm".
            - The message in the linter message should indicate 
                a missing operator between term and parenthesis.
            - The position in the linter message should be (5, 6).
        """
        tokens = [("term1", (0, 5)), ("(", (5, 6))]
        linter = QueryLinter("term1 (query)", self.linter_messages)
        self.assertTrue(linter.check_order_of_tokens(tokens, "term1", (0, 5), 0))
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "ParenthesisAfterTerm")
        self.assertEqual(
            self.linter_messages[0]['message'],
            "Missing Operator between term and parenthesis."
        )
        self.assertEqual(self.linter_messages[0]['position'], (0, 5))

    def test_missing_operator_between_parentheses(self):
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
            - The rule in the linter message should be "MissingOperatorBetweenParenthesis".
            - The message in the linter message should indicate 
                a missing operator between closing and opening parenthesis.
            - The position in the linter message should be (5, 6).
        """
        tokens = [(")", (0, 5)), ("(", (5, 6))]
        linter = QueryLinter(") (query)", self.linter_messages)
        self.assertTrue(linter.check_order_of_tokens(tokens, ")", (0, 5), 0))
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "MissingOperatorBetweenParenthesis")
        self.assertEqual(
            self.linter_messages[0]['message'],
            "Missing Operator between closing and opening parenthesis."
        )
        self.assertEqual(self.linter_messages[0]['position'], (0, 5))

    def test_missing_operator_between_term_and_search_field(self):
        """
        Test case for detecting missing operator between term and search field in a query string.

        This test initializes a QueryLinter object with a query string containing
        a term followed by a search field without an operator in between.
        It verifies that the linter messages contain the appropriate rule, message, and position
        for the missing operator.

        Assertions:
            - The linter should detect the missing operator between term and search field.
            - The linter messages list should contain exactly one message.
            - The rule in the linter message should be "SearchFieldAfterTerm".
            - The message in the linter message should 
                indicate a missing operator between term and search field.
            - The position in the linter message should be (5, 10).
        """
        tokens = [("term1", (0, 5)), ("au=", (5, 8))]
        linter = QueryLinter("term1 field1", self.linter_messages)
        self.assertTrue(linter.check_order_of_tokens(tokens, "term1", (0, 5), 0))
        self.assertEqual(len(self.linter_messages), 1)
        self.assertEqual(self.linter_messages[0]['rule'], "SearchFieldAfterTerm")
        self.assertEqual(
            self.linter_messages[0]['message'],
            "Missing Operator between term and search field."
        )
        self.assertEqual(self.linter_messages[0]['position'], (0, 5))

if __name__ == '__main__':
    unittest.main()
