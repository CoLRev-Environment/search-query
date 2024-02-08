#!/usr/bin/env python
"""Tests for the Query"""
from search_query.query import Query
from search_query.or_query import OR_Query
from search_query.and_query import AND_Query
from search_query.tree import Tree
from search_query.node import Node

import unittest

class TestQuery(unittest.TestCase):
    
    def testSimpleQuery(self) -> None:
        querySimple = OR_Query("[dog, cat]",[])
        self.assertEqual("dog", querySimple.qt.root.children[0].value)
        self.assertEqual("cat", querySimple.qt.root.children[1].value)
        self.assertEqual("OR", querySimple.qt.root.value)
        return
        
        
    def testNestedStructure(self) ->None:
        queryPets = OR_Query("[dog, cat]",[])    
        queryComplete = AND_Query("[elephant]",[queryPets])
        
        for c in queryComplete.qt.root.children:
            print(c.value)
        
        self.assertEqual(queryComplete.qt.root.children[1].value, queryPets.qt.root.value)
        return
    
    def testNestedStructureMultipleQueries(self) ->None:
        queryPets = OR_Query("[dog, cat]",[])    
        queryAnimals = OR_Query("[elephant, giraffe]",[])  
        queryComplete = AND_Query("",[queryPets, queryAnimals])
        
        print(f"PRINT: {queryComplete.printQuery(queryComplete.qt.root)}")
            
        
        self.assertEqual(queryComplete.qt.root.children[1].value, queryPets.qt.root.value)
        return
    
    def testPrintQuery(self) -> None:
        queryAI=OR_Query("[ai, artificial intelligence, machine learning]",[])
        queryHealth=OR_Query("[health care, medicine]", [])
        queryEthics=OR_Query("[ethic*, moral*]", [])
        queryValues=AND_Query("[values]", [queryEthics])
        queryComplete=AND_Query("", [queryAI, queryHealth, queryValues])
        
        print(f"PRINT: {queryComplete.printQuery(queryComplete.qt.root)}")
        
        return
    
    """def testValidInput(self)->None:
        queryPets = OR_Query("!dog, cat",[])
        print(queryPets.qs)
        return

    Example:
    def test_parse() -> None:
        query = search_query.query.Query()
        query.parse(query_string="(digital OR online) AND work")

        actual_list = query.get_linked_list()

        expected_list = {1: "digital", 2: "online", 3: "1 OR 2", 4: "work", 5: "3 AND 4"}
        assert actual_list == expected_list"""

if __name__=='__main__':
	unittest.main()
