#!/usr/bin/env python
"""Tests for the Query"""
from search_query.or_query import OR_Query
from search_query.and_query import AND_Query
from search_query.not_query import NOT_Query

import unittest

class TestQuery(unittest.TestCase):
    
    def setUp(self) -> None:
        self.queryRobot=NOT_Query("[robot*]",[],"Author Keywords")
        self.queryAI=OR_Query("['AI', 'Artificial Intelligence', 'Machine Learning']",[self.queryRobot],"Author Keywords")
        self.queryHealth=OR_Query(f"['health care', 'medicine']", [],"Author Keywords")
        self.queryEthics=OR_Query(f"[ethic*, moral*]", [],"Abstract")
        self.queryComplete=AND_Query("", [self.queryAI, self.queryHealth, self.queryEthics],"Author Keywords")
        
        return
    
    def testJSONWoS(self):
        
        self.queryComplete.translateWebOfScience()
        print("TRANSLATED WOS: "+self.queryComplete.printQueryWoS(self.queryComplete.qt.root))
        print("TRANSLATED IEEE: "+self.queryComplete.printQueryIEEE(self.queryComplete.qt.root))
        
        return 

        
        
       
if __name__=='__main__':
	unittest.main()
