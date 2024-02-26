#!/usr/bin/env python
"""Tests for the Query"""
import unittest

from search_query.and_query import AndQuery
from search_query.node import Node
from search_query.not_query import NotQuery
from search_query.or_query import OrQuery


class TestQuery(unittest.TestCase):
    """Testing class."""

    def setUp(self) -> None:
        self.testNode = Node("testvalue", False, "Document Title")

        self.queryRobot = NotQuery("[robot*]", [], "Author Keywords")
        self.queryAI = OrQuery(
            "['AI', 'Artificial Intelligence', 'Machine Learning']",
            [self.queryRobot],
            "Author Keywords",
        )
        self.queryHealth = OrQuery("['health care', 'medicine']", [], "Author Keywords")
        self.queryEthics = OrQuery("[ethic*, moral*]", [], "Abstract")
        self.queryComplete = AndQuery(
            "", [self.queryAI, self.queryHealth, self.queryEthics], "Author Keywords"
        )

        return

    def test_print_node(self):
        expected = "value: testvalue operator: False search field: Document Title"
        self.assertEqual(
            self.testNode.print_node(), expected, "Print Node Method does not work."
        )
        return

    # test whether the children are appended correctly
    def test_append_children(self):
        healthCareChild = Node("'health care'", False, "Author Keywords")
        medicineChild = Node("medicine", False, "Author Keywords")
        expected = [healthCareChild, medicineChild]
        self.assertEqual(
            self.queryHealth.query_tree.root.children[0].print_node(),
            expected[0].print_node(),
            "Children were appended incorrectly!",
        )
        self.assertEqual(
            self.queryHealth.query_tree.root.children[0].print_node(),
            expected[0].print_node(),
            "Children were appended incorrectly!",
        )
        return

    # test whether OR node is created correctly
    def test_or_query(self):
        expected = Node("OR", True, "")
        self.assertEqual(
            self.queryAI.query_tree.root.print_node(),
            expected.print_node(),
            "OR root was not created correctly!",
        )

        return

    # test whether AND node is created correctly
    def test_and_query(self):
        expected = Node("AND", True, "")
        self.assertEqual(
            self.queryComplete.query_tree.root.print_node(),
            expected.print_node(),
            "AND root was not created correctly!",
        )
        return

    # test whether NOT node is created correctly
    def test_not_query(self):
        expected = Node("NOT", True, "")
        self.assertEqual(
            self.queryRobot.query_tree.root.print_node(),
            expected.print_node(),
            "NOT root was not created correctly!",
        )
        return

    # test whether roots of nested Queries are appended as children
    def test_nested_queries(self):
        self.assertListEqual(
            self.queryComplete.query_tree.root.children,
            [
                self.queryAI.query_tree.root,
                self.queryHealth.query_tree.root,
                self.queryEthics.query_tree.root,
            ],
            "Nested Queries were not appended correctly!",
        )
        return

    # test whether the translation of the tool is identical to the manually translated WoS Query
    def test_translation_WoS(self):
        expected = "(AK=('AI' OR 'Artificial Intelligence' OR 'Machine Learning' NOT robot*) AND AK=('health care' OR 'medicine') AND AB=(ethic* OR moral*))"
        self.assertEqual(
            self.queryComplete.print_query_wos(self.queryComplete.query_tree.root),
            expected,
            "Query was not translated to Web of Science Syntax",
        )
        return

    # test whether the translation of the tool is identical to the manually translated IEEE Query
    def test_translation_IEEE(self):
        expected = "(('Author Keywords':'AI' OR 'Author Keywords':'Artificial Intelligence' OR 'Author Keywords':'Machine Learning') NOT 'Author Keywords':robot*) AND ('Author Keywords':'health care' OR 'Author Keywords':'medicine') AND ('Abstract':ethic* OR 'Abstract':moral*)"
        self.assertEqual(
            self.queryComplete.print_query_ieee(self.queryComplete.query_tree.root),
            expected,
            "Query was not translated to IEEE Syntax",
        )
        return

    # test failures
    # test whether the validation method correctly throws an Exception if an invalid tree (including a circle) is created
    def testTreeValidationWithInvalidTree(self):
        AndQuery("[invalid, tree]", [self.queryComplete, self.queryAI], "Abstract")

        return


if __name__ == "__main__":
    unittest.main()
