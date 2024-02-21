#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations
from search_query.node import Node
import json
import datetime

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


    #translating method for Web of Science database
    #creates a JSON file with translation information at ../translations/WoS/translationWoS_ddMMYYYY_HH:MM 
    def translateWebOfScience(self):
        data= {
            "database":"Web of Science - Core Collection",
            "url":"https://www.webofscience.com/wos/woscc/advanced-search",
            "translatedQuery" : f"({self.get_searchField_WoS(self.searchField)}={self.printQueryWoS(self.qt.root)})",
            "annotations" : "Paste the translated string without quotation marks into the advanced search free text field.",
            "API":"possible"    
        }
        
        with open(f'../translations/WoS/translationWoS_{datetime.datetime.now().strftime("%d-%m-%Y_%H:%M")}.json', 'w') as f:
            json.dump(data, f)
    
    #actual translation logic for WoS  
    def printQueryWoS(self, startNode):
        result=""
        for c in startNode.children:
            
            #startNode is not an operator
            if(c.operator==False):
                
                #current element is first but not only child element --> operator does not need to be appended again
                if((c==startNode.children[0]) & (c!=startNode.children[-1])):
                    result=f"{result}{self.get_searchField_WoS(c.searchField)}=({c.value}" 
                
                #current element is not first child    
                else:
                    result=f"{result} {startNode.value} {c.value}"  
                
                #current Element is last Element -> closing parenthesis    
                if (c==startNode.children[-1]):
                   result=f"{result})" 
            
            #startNode is operator Node   
            else:
                #current element is NOT Operator -> no parenthesis in WoS 
                if(c.value=="NOT"):
                    result=f"{result}{self.printQueryWoS(c)}"
                
                elif(((c==startNode.children[0] )& (c!=startNode.children[-1]))):
                    result=f"{result}({self.printQueryWoS(c)}"
                else:
                    result=f"{result} {startNode.value} {self.printQueryWoS(c)}"
                    
                if ((c==startNode.children[-1]) & (c.value!="NOT")):
                   result=f"{result})"                
        return f"{result}"
    
    #translating method for Web of Science database
    #creates a JSON file with translation information at ../translations/IEEE/translationIEEE_ddMMYYYY_HH:MM 
    def translateIEEE(self):
        data= {
            "database":"IEEE Xplore",
            "url":"https://ieeexplore.ieee.org/search/advanced/command",
            "translatedQuery" : f"{self.printQueryIEEE(self.qt.root)}",
            "annotations" : "Paste the translated string without quotation marks into the command search free text field.",
            "API":"possible"    
        }
        
        with open(f'../translations/IEEE/translationIEEE_{datetime.datetime.now().strftime("%d-%m-%Y_%H:%M")}.json', 'w') as f:
            json.dump(data, f)
            
    #actual translation logic for IEEE
    def printQueryIEEE(self, startNode):
        result=""
        for index, c in enumerate(startNode.children):
            
            #startNode is not an operator
            if(c.operator==False):
                
                #current element is first but not only child element --> operator does not need to be appended again
                if((c==startNode.children[0]) & (c!=startNode.children[-1])):
                    result=f"{result}('{c.searchField}':{c.value}" 
                    if (startNode.children[index+1].operator==True):
                        result=f"({result})" 
                
                #current element is not first child    
                else:
                    result=f"{result} {startNode.value} '{c.searchField}':{c.value}" 
                    if (c!=startNode.children[-1]):        
                        if (startNode.children[index+1].operator==True):
                            result=f"({result})"
                
                #current element is last Element -> closing parenthesis    
                if (c==startNode.children[-1]):
                   result=f"{result})" 
            
            #startNode is operator Node   
            else:
                #current element is NOT operator -> no parenthesis in WoS 
                if(c.value=="NOT"):
                    result=f"{result}{self.printQueryIEEE(c)}"
                
                #current Element is OR/AND operator:
                elif(((c==startNode.children[0] )& (c!=startNode.children[-1]))):
                    result=f"{result}{self.printQueryIEEE(c)}"
                else:
                    result=f"{result} {startNode.value} {self.printQueryIEEE(c)}"
                                   
        return f"{result}"
    
    def get_searchField_WoS (self, sf) -> str:
    
        if sf=="Author Keywords": return "AK"
        if sf=="Abstract": return "AB"
        if sf=="Author": return "AU"
        if sf=="DOI": return "DO" 
        if sf=="ISBN/ISSN": return "IS"
        if sf=="Publisher": return "PUBL"
        if sf=="Publication Title": return "SO"
        if sf=="Title": return "TI"
        
    
    
    def get_linked_list(self) -> dict:
        # generate linked_list from query_tree
        linked_list = {}
        return linked_list
