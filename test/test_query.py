#!/usr/bin/env python
"""Tests for the Query"""
import unittest

from search_query.and_query import AND_Query
from search_query.not_query import NOT_Query
from search_query.or_query import OR_Query
from search_query.node import Node


class TestQuery(unittest.TestCase):
    def setUp(self) -> None:
        self.testNode = Node("testvalue", False, "Document Title")
        
        self.queryRobot = NOT_Query("[robot*]", [], "Author Keywords")
        self.queryAI = OR_Query(
            "['AI', 'Artificial Intelligence', 'Machine Learning']",
            [self.queryRobot],
            "Author Keywords",
        )
        self.queryHealth = OR_Query(
            "['health care', 'medicine']", [], "Author Keywords"
        )
        self.queryEthics = OR_Query("[ethic*, moral*]", [], "Abstract")
        self.queryComplete = AND_Query(
            "", [self.queryAI, self.queryHealth, self.queryEthics], "Author Keywords"
        )

        return
    
    def testPrintNode(self):
        expected="value: testvalue operator: False search field: Document Title"
        self.assertEqual(self.testNode.printNode(), expected, "Print Node Method does not work.")
        return
    
    #test whether the children are appended correctly
    def testAppendChildren(self):
        healthCareChild=Node("'health care'", False, "Author Keywords")
        medicineChild=Node("medicine", False, "Author Keywords")
        expected=[healthCareChild,medicineChild]
        self.assertEqual(self.queryHealth.qt.root.children[0].printNode(),expected[0].printNode(),"Children were apended incorrectly!")
        self.assertEqual(self.queryHealth.qt.root.children[0].printNode(),expected[0].printNode(),"Children were apended incorrectly!")
        return
    
    def testORQuery(self):
        expected=Node("OR",True,"")
        self.assertEqual(self.queryAI.qt.root.printNode(),expected.printNode(),"OR root was not created correctly!")
        
        return
    
    def testAndQuery(self):
        expected=Node("AND",True,"")
        self.assertEqual(self.queryComplete.qt.root.printNode(),expected.printNode(),"AND root was not created correctly!")
        return
    
    def testNotQuery(self):
        expected=Node("NOT",True,"")
        self.assertEqual(self.queryRobot.qt.root.printNode(),expected.printNode(),"NOT root was not created correctly!")
        return
    
    def testNestedQueries(self):
        self.assertListEqual(self.queryComplete.qt.root.children, [self.queryAI.qt.root, self.queryHealth.qt.root, self.queryEthics.qt.root],
                             "Nested Queries were not appended correctly!")
        return
    
    def testTranslationWoS(self):
        expected="(AK=('AI' OR 'Artificial Intelligence' OR 'Machine Learning' NOT robot*) AND AK=('health care' OR 'medicine') AND AB=(ethic* OR moral*))"
        self.assertEqual(self.queryComplete.printQueryWoS(self.queryComplete.qt.root), expected, "Query was not translated to Web of Science Syntax")
        return
    
    def testTranslationIEEE(self):
        expected="(('Author Keywords':'AI' OR 'Author Keywords':'Artificial Intelligence' OR 'Author Keywords':'Machine Learning') NOT 'Author Keywords':robot*) AND ('Author Keywords':'health care' OR 'Author Keywords':'medicine') AND ('Abstract':ethic* OR 'Abstract':moral*)"
        self.assertEqual(self.queryComplete.printQueryIEEE(self.queryComplete.qt.root), expected, "Query was not translated to IEEE Syntax")
        return
    
    #test failures

    def testTreeValidationWithInvalidTree(self):
        
        queryInvalid= AND_Query("[invalid, tree]", [self.queryComplete,self.queryAI],"Abstract")
        
        return


if __name__ == "__main__":
    unittest.main()
