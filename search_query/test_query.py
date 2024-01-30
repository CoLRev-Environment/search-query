#!/usr/bin/env python
"""Tests for the Query"""
from query import Query
from or_query import OR_Query
from and_query import AND_Query
from tree import Tree
from node import Node

import unittest

class TestQuery(unittest.TestCase):
        
        
    def testNestedeStructure(self) ->None:
        queryPets = OR_Query("[dog, cat]",[])
            
        queryComplete = AND_Query("[elephant]",[queryPets])
        
        for c in queryComplete.qt.root.children:
            print(c.value)
        
        self.assertEqual(queryComplete.qt.root.children[1].value, queryPets.qt.root.value)
        return

    """Example:
    def test_parse() -> None:
        query = search_query.query.Query()
        query.parse(query_string="(digital OR online) AND work")

        actual_list = query.get_linked_list()

        expected_list = {1: "digital", 2: "online", 3: "1 OR 2", 4: "work", 5: "3 AND 4"}
        assert actual_list == expected_list"""

if __name__=='__main__':
	unittest.main()
