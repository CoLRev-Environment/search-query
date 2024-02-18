#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations
from search_query.node import Node
import json



class Query:
    
    # validate input to test if a valid tree structure can be guaranteed    
    def validTreeStructure(self, startNode) -> bool:
        if(startNode.marked):
            return False
        else:
            startNode.marked=True
            for c in startNode.children:
                self.validTreeStructure(c)
        return True
        

    # parse the query provided, build nodes&tree structure
    def buildQueryTree(self):
        # append Strings provided in Query Strings (qs) as children to current Query
        if self.qs != "":
            childrenString = self.qs[self.qs.find("[") :]
            childrenList = childrenString[1:-1].split(", ")
            self.createTermNodes(childrenList, self.searchField)

        # append root of every Query in nestedQueries as a child to the current Query
        if self.nestedQueries != []:
            for q in self.nestedQueries:
                self.qt.root.children.append(q.qt.root)

        return

    # build children term nodes, append to tree
    def createTermNodes(self, childrenList, searchField) -> None:
        for item in childrenList:
            termNode = Node(item, False, searchField)
            self.qt.root.children.append(termNode)
        return

    #prints query in PreNotation
    def printQuery(self, startNode) -> str:
        result = ""
        result = f"{result}{startNode.value}"
        if startNode.children == []:
            return result
        else:
            result = f"{result}["
            for child in startNode.children:
                result = f"{result}{self.printQuery(child)}"
                if child != startNode.children[-1]:
                    result = f"{result}, "
        return f"{result}]"

    # TODO implement translating logic
    #((AK=("AI"OR "Artificial Intelligence" OR "Machine learning" NOT robot*)) AND AK=("health care" OR medicine)) AND AB=(moral* OR ethic*)
    # AND[OR["AI", "Artificial Intelligence", "Machine Learning", NOT[robot*]], OR["health care", "medicine"], OR[ethic*, moral*]]
    def translateWebOfScience(self):
        value= {
            "translatedQuery" : f"{self.printQuery(self.qt.root)}",
            "annotations" : "hihi",
            "API":"possible"    
        }
        
        return json.dumps(value)
    
    def printQueryWoS(self, startNode):
        result=""
        for c in startNode.children:
            if(c.operator==False):
                if(c!=startNode.children[-1]):
                    result=f"{result}{c.value} {startNode.value} "
                else:
                   result=f"{result}{c.value} " 
                
                
            else:
                if(c!=startNode.children[-1]):
                    result=f"{result} {self.printQueryWoS(c)} {startNode.value}"
                else:
                    result=f"{result} {self.printQueryWoS(c)})"
                    
                
        return f"{result}"
        
    
    def printWoS(self, startNode):
       return  self.printQueryWoS(startNode)
    
    
    # TODO implement translating logic
    def translateDB2(self) -> str:
        # parameter: database/syntax?
        query_str = ""
        return query_str

    def get_linked_list(self) -> dict:
        # generate linked_list from query_tree
        linked_list = {}
        return linked_list
