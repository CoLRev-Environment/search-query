#!/usr/bin/env python
"""Tests for the Query"""
from search_query.or_query import OR_Query
from search_query.and_query import AND_Query

import unittest

class TestQuery(unittest.TestCase):
    
    def setUp(self) -> None:
        self.queryAI=OR_Query("[ai, artificial intelligence, machine learning]",[])
        self.queryHealth=OR_Query("[health care, medicine]", [])
        self.queryEthics=OR_Query("[ethic*, moral*]", [])
        self.queryValues=AND_Query("[values]", [self.queryEthics])
        self.queryComplete=AND_Query("", [self.queryAI, self.queryHealth, self.queryValues])
        
        return
    
    
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
        
        self.assertEqual("AND[OR[ai, artificial intelligence, machine learning], OR[health care, medicine], AND[values, OR[ethic*, moral*]]]",
                         self.queryComplete.printQuery(self.queryComplete.qt.root),
                         "Print Statement is not equal!")
        
        return
    
    def testTreeStructure(self):
        return
       
if __name__=='__main__':
	unittest.main()
