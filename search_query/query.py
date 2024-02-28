#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import datetime
import json
from abc import ABC, abstractmethod

from search_query.node import Node
from search_query.tree import Tree



class Query(ABC):
    """Query class."""

    @abstractmethod
    def __init__(self, search_terms, nested_queries, search_field):
       pass
   
    def valid_tree_structure(self, start_node) -> bool:
        """validate input to test if a valid tree structure can be guaranteed"""

        if start_node.marked:
            return False

        start_node.marked = True
        if start_node.children != []:
            for child in start_node.children:
                return self.valid_tree_structure(child)
        return True

    def build_query_tree(self) -> None:
        """parse the query provided, build nodes&tree structure"""
        if self.search_terms != []:
            # append Strings provided in search_terms (query_string) as children to current Query
            self.create_term_nodes(self.search_terms, self.search_field)

        if self.nested_queries != []:
            # append root of every Query in nested_queries as a child to the current Query
            for query in self.nested_queries:
                self.query_tree.root.children.append(query.query_tree.root)

    def create_term_nodes(self, children_list, search_field) -> None:
        """build children term nodes, append to tree"""
        for item in children_list:
            term_node = Node(item, False, search_field)
            self.query_tree.root.children.append(term_node)

    def print_query(self, start_node) -> str:
        """prints query in PreNotation"""
        result = ""
        result = f"{result}{start_node.value}"
        if start_node.children == []:
            return result

        result = f"{result}["
        for child in start_node.children:
            result = f"{result}{self.print_query(child)}"
            if child != start_node.children[-1]:
                result = f"{result}, "
        return f"{result}]"

    def translate_wos(self,file_name) -> None:
        """translating method for Web of Science database
        creates a JSON file with translation information at
        ../translations/WoS/file_name
        """
        data = {
            "database": "Web of Science - Core Collection",
            "url": "https://www.webofscience.com/wos/woscc/advanced-search",
            "translatedQuery": f"{self.print_query_wos(self.query_tree.root)}",
            "annotations": "Paste the translated string without quotation marks into the advanced search free text field."
        }

        json_object = json.dumps(data, indent=4)
        
        with open(f'../translations/WoS/{file_name}.json',"w") as file:
            file.write(json_object)

    def print_query_wos(self, start_node) -> str:
        """actual translation logic for WoS"""
        result = ""
        for child in start_node.children:
            if child.operator is False:
                # start_node is not an operator
                if (child == start_node.children[0]) & (
                    child != start_node.children[-1]
                ):
                    # current element is first but not only child element
                    # -->operator does not need to be appended again
                    result = f"{result}{self.get_search_field_wos(child.search_field)}=({child.value}"

                else:
                    # current element is not first child
                    result = f"{result} {start_node.value} {child.value}"

                if child == start_node.children[-1]:
                    # current Element is last Element -> closing parenthesis
                    result = f"{result})"

            else:
                # start_node is operator node
                if child.value == "NOT":
                    # current element is NOT Operator -> no parenthesis in WoS
                    result = f"{result}{self.print_query_wos(child)}"

                elif (child == start_node.children[0]) & (
                    child != start_node.children[-1]
                ):
                    result = f"{result}({self.print_query_wos(child)}"
                else:
                    result = (
                        f"{result} {start_node.value} {self.print_query_wos(child)}"
                    )

                if (child == start_node.children[-1]) & (child.value != "NOT"):
                    result = f"{result})"
        return f"{result}"

    def translate_ieee(self, file_name) -> None:
        """translating method for IEEE Xplore database
        creates a JSON file with translation information at
        ../translations/IEEE/translationIEEE_ddMMYYYY_HH:MM
        """
        data = {
            "database": "IEEE Xplore",
            "url": "https://ieeexplore.ieee.org/search/advanced/command",
            "translatedQuery": f"{self.print_query_ieee(self.query_tree.root)}",
            "annotations": "Paste the translated string without quotation marks into the command search free text field."
        }

        json_object = json.dumps(data, indent=4)
        
        with open(f'../translations/IEEE/{file_name}.json',"w") as file:
            file.write(json_object)

    def print_query_ieee(self, start_node) -> str:
        """actual translation logic for IEEE"""
        result = ""
        for index, child in enumerate(start_node.children):
            # start_node is not an operator
            if child.operator is False:
                # current element is first but not only child element
                # --> operator does not need to be appended again
                if (child == start_node.children[0]) & (
                    child != start_node.children[-1]
                ):
                    result = f"{result}(\"{child.search_field}\":{child.value}"
                    if start_node.children[index + 1].operator is True:
                        result = f"({result})"

                else:
                    # current element is not first child
                    result = f"{result} {start_node.value} \"{child.search_field}\":{child.value}"
                    if child != start_node.children[-1]:
                        if start_node.children[index + 1].operator is True:
                            result = f"({result})"

                if child == start_node.children[-1]:
                    # current element is last Element -> closing parenthesis
                    result = f"{result})"

            else:
                # start_node is operator Node
                if (child == start_node.children[0]) & (
                    child != start_node.children[-1]
                ):
                    # current Element is OR/AND operator:
                    result = f"{result}{self.print_query_ieee(child)}"
                else:
                    result = f"{result} {start_node.value} {self.print_query_ieee(child)}"
        
        return f"{result}"

    def get_search_field_wos(self, search_field) -> str:
        if search_field == "Author Keywords":
            result = "AK"
        elif search_field == "Abstract":
            result = "AB"
        elif search_field == "Author":
            result = "AU"
        elif search_field == "DOI":
            result = "DO"
        elif search_field == "ISBN/ISSN":
            result = "IS"
        elif search_field == "Publisher":
            result = "PUBL"
        elif search_field == "Title":
            result = "TI"
        return result

    def translate_pubmed(self, file_name) -> None:
        """translating method for PubMed database
        creates a JSON file with translation information at
        ../translations/PubMed/file_name
        """
        data = {
            "database": "PubMed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/advanced/",
            "translatedQuery": f"{self.print_query_pubmed(self.query_tree.root)}",
            "annotations": "Paste the translated string without quotation marks into the \"Query Box\" free text field."
        }

        json_object = json.dumps(data, indent=4)
        
        with open(f'../translations/PubMed/{file_name}.json',"w") as file:
            file.write(json_object)

    def print_query_pubmed(self, start_node) -> str:
        """actual translation logic for PubMed"""
        result = ""
        for child in start_node.children:
            if child.operator is False:
                # start_node is not an operator
                if (child == start_node.children[0]) & (
                    child != start_node.children[-1]
                ):
                    # current element is first but not only child element
                    # -->operator does not need to be appended again
                    result = f"{result}({child.value}[{self.get_search_field_pubmed(child.search_field)}]"

                else:
                    # current element is not first child
                    result = f"{result} {start_node.value} {child.value}[{self.get_search_field_pubmed(child.search_field)}]"

                if child == start_node.children[-1]:
                    # current Element is last Element -> closing parenthesis
                    result = f"{result})"

            else:
                # start_node is operator node
                if child.value == "NOT":
                    # current element is NOT Operator -> no parenthesis in WoS
                    result = f"{result}{self.print_query_pubmed(child)}"

                elif (child == start_node.children[0]) & (
                    child != start_node.children[-1]
                ):
                    result = f"{result}({self.print_query_pubmed(child)}"
                else:
                    result = (
                        f"{result} {start_node.value} {self.print_query_pubmed(child)}"
                    )

                if (child == start_node.children[-1]) & (child.value != "NOT"):
                    result = f"{result})"
        return f"{result}"

    def get_search_field_pubmed(self, search_field) -> str:
        if search_field == "Author Keywords":
            result = "ot"
        elif search_field == "Abstract":
            result = "tiab"
        elif search_field == "Author":
            result = "au"
        elif search_field == "DOI":
            result = "aid"
        elif search_field == "ISBN/ISSN":
            result = "isbn"
        elif search_field == "Publisher":
            result = "pubn"
        elif search_field == "Title":
            result = "ti"
        return result

