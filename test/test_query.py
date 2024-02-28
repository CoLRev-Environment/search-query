#!/usr/bin/env python
"""Tests for search query translation"""
import unittest
from search_query.and_query import AndQuery
from search_query.node import Node
from search_query.not_query import NotQuery
from search_query.or_query import OrQuery


class TestQuery(unittest.TestCase):
    """Testing class."""

    def setUp(self):
        self.test_node = Node("testvalue", False, "Document Title")
        self.query_robot = NotQuery(["robot*"], [], "Author Keywords")
        self.query_ai = OrQuery(
            ["\"AI\"", "\"Artificial Intelligence\"", "\"Machine Learning\""],
            [self.query_robot],
            "Author Keywords",
        )
        self.queryHealth = OrQuery(["\"health care\"", "medicine"], [], "Author Keywords")
        self.queryEthics = OrQuery(["ethic*", "moral*"], [], "Abstract")
        self.queryComplete = AndQuery([], [self.query_ai, self.queryHealth, self.queryEthics], "Author Keywords")

    def test_print_node(self) -> None:
        expected = "value: testvalue operator: False search field: Document Title"
        self.assertEqual(
            self.test_node.print_node(), expected, "Print Node Method does not work."
        )

    # test whether the children are appended correctly
    def test_append_children(self) -> None:
        healthCareChild = Node("\"health care\"", False, "Author Keywords")
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

    # test whether OR node is created correctly
    def test_or_query(self) -> None:
        expected = Node("OR", True, "")
        self.assertEqual(
            self.query_ai.query_tree.root.print_node(),
            expected.print_node(),
            "OR root was not created correctly!",
        )

    # test whether AND node is created correctly
    def test_and_query(self) -> None:
        expected = Node("AND", True, "")
        self.assertEqual(
            self.queryComplete.query_tree.root.print_node(),
            expected.print_node(),
            "AND root was not created correctly!",
        )

    # test whether NOT node is created correctly
    def test_not_query(self) -> None:
        expected = Node("NOT", True, "")
        self.assertEqual(
            self.query_robot.query_tree.root.print_node(),
            expected.print_node(),
            "NOT root was not created correctly!",
        )

    # test whether roots of nested Queries are appended as children
    def test_nested_queries(self) -> None:
        self.assertListEqual(
            self.queryComplete.query_tree.root.children,
            [
                self.query_ai.query_tree.root,
                self.queryHealth.query_tree.root,
                self.queryEthics.query_tree.root,
            ],
            "Nested Queries were not appended correctly!",
        )

    # test whether the translation of the tool is identical to the manually translated WoS Query
    def test_translation_WoS(self) -> None:
        expected = "(AK=(\"AI\" OR \"Artificial Intelligence\" OR \"Machine Learning\" NOT robot*) AND AK=(\"health care\" OR medicine) AND AB=(ethic* OR moral*))"
        self.assertEqual(
            self.queryComplete.print_query_wos(self.queryComplete.query_tree.root),
            expected,
            "Query was not translated to Web of Science Syntax",
        )

    # test whether the translation of the tool is identical to the manually translated IEEE Query
    def test_translation_IEEE(self) -> None:
        expected = "((\"Author Keywords\":\"AI\" OR \"Author Keywords\":\"Artificial Intelligence\" OR \"Author Keywords\":\"Machine Learning\") OR  NOT \"Author Keywords\":robot*) AND (\"Author Keywords\":\"health care\" OR \"Author Keywords\":medicine) AND (\"Abstract\":ethic* OR \"Abstract\":moral*)"
        self.assertEqual(
            self.queryComplete.print_query_ieee(self.queryComplete.query_tree.root),
            expected,
            "Query was not translated to IEEE Syntax",
        )
        
    def test_translation_pubmed(self) -> None:
        expected = "((\"AI\"[ot] OR \"Artificial Intelligence\"[ot] OR \"Machine Learning\"[ot] NOT robot*[ot]) AND (\"health care\"[ot] OR medicine[ot]) AND (ethic*[tiab] OR moral*[tiab]))"
        self.assertEqual(
            self.queryComplete.print_query_pubmed(self.queryComplete.query_tree.root),
            expected,
            "Query was not translated to PubMed Syntax",
        )

    def test(self) -> None:
        """test"""
        self.queryComplete.translate_ieee("ieeeTest")
        self.queryComplete.translate_pubmed("pubmedTest")
        self.queryComplete.translate_wos("wosTest")


if __name__ == "__main__":
    unittest.main()
