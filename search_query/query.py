#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import json
from abc import ABC
from abc import abstractmethod

from search_query.node import Node


class Query(ABC):
    """Query class."""

    @abstractmethod
    def __init__(
        self, search_terms: list[str], nested_queries: list[Query], search_field: str
    ):
        """init method - abstract"""

    def valid_tree_structure(self, start_node: Node):
        """validate input to test if a valid tree structure can be guaranteed"""
        if start_node.marked is True:
            raise ValueError("Building Query Tree failed")
        start_node.marked = True
        if start_node.children == []:
            pass
        for child in start_node.children:
            self.valid_tree_structure(child)
        return True

    def build_query_tree(
        self, search_terms: list[str], nested_queries: list[Query], search_field: str
    ) -> None:
        """parse the query provided, build nodes&tree structure"""
        if (
            search_terms != []
        ):  # append strings provided in search_terms (query_string) as children to current Query
            self.create_term_nodes(search_terms, search_field)

        if nested_queries != []:
            # append root of every Query in nested_queries as a child to the current Query
            for query in nested_queries:
                self.query_tree.root.children.append(query.query_tree.root)

    def create_term_nodes(self, children_list: list[str], search_field: str) -> None:
        """build children term nodes, append to tree"""
        for item in children_list:
            term_node = Node(item, False, search_field)
            self.query_tree.root.children.append(term_node)

    def print_query(self, start_node: Node) -> str:
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

    def translate_wos(self, file_name: str) -> None:
        """translating method for Web of Science database
        creates a JSON file with translation information at
        ../translations/WoS/file_name
        """
        data = {
            "database": "Web of Science - Core Collection",
            "url": "https://www.webofscience.com/wos/woscc/advanced-search",
            "translatedQuery": f"{self.print_query_wos(self.query_tree.root)}",
            "annotations": "Paste the translated string without quotation marks into the advanced search free text field.",
        }

        json_object = json.dumps(data, indent=4)

        with open(
            f"./translations/WoS/{file_name}.json", "w", encoding="utf-8"
        ) as file:
            file.write(json_object)

    def print_query_wos(self, start_node: Node) -> str:
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

    def translate_ieee(self, file_name: str) -> None:
        """translating method for IEEE Xplore database
        creates a JSON file with translation information at
        ../translations/IEEE/translationIEEE_ddMMYYYY_HH:MM
        """
        data = {
            "database": "IEEE Xplore",
            "url": "https://ieeexplore.ieee.org/search/advanced/command",
            "translatedQuery": f"{self.print_query_ieee(self.query_tree.root)}",
            "annotations": "Paste the translated string without quotation marks into the command search free text field.",
        }

        json_object = json.dumps(data, indent=4)

        with open(
            f"./translations/IEEE/{file_name}.json", "w", encoding="utf-8"
        ) as file:
            file.write(json_object)

    def print_query_ieee(self, start_node: Node) -> str:
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
                    result = f'{result}("{child.search_field}":{child.value}'
                    if start_node.children[index + 1].operator is True:
                        result = f"({result})"

                else:
                    # current element is not first child
                    result = f'{result} {start_node.value} "{child.search_field}":{child.value}'
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
                    result = (
                        f"{result} {start_node.value} {self.print_query_ieee(child)}"
                    )

        return f"{result}"

    def get_search_field_wos(self, search_field: str) -> str:
        """transform search field to WoS Syntax"""
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

    def translate_pubmed(self, file_name: str) -> None:
        """translating method for PubMed database
        creates a JSON file with translation information at
        ../translations/PubMed/file_name
        """
        data = {
            "database": "PubMed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/advanced/",
            "translatedQuery": f"{self.print_query_pubmed(self.query_tree.root)}",
            "annotations": 'Paste the translated string without quotation marks into the "Query Box" free text field.',
        }

        json_object = json.dumps(data, indent=4)

        with open(
            f"./translations/PubMed/{file_name}.json", "w", encoding="utf-8"
        ) as file:
            file.write(json_object)

    def print_query_pubmed(self, start_node: Node) -> str:
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
                    # current element is NOT Operator -> no parenthesis in PubMed
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

    def get_search_field_pubmed(self, search_field: str) -> str:
        """transform search field to PubMed Syntax"""
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
