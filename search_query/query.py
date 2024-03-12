#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import json
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import List
from typing import Optional
from typing import Union

from search_query.node import Node


class Query(ABC):
    """Query class."""

    query_node: Node

    @abstractmethod
    def __init__(
        self,
        *,
        operator: str,
        children: List[Union[str, Query]],
        search_field: str,
    ):
        """init method - abstract"""

        self._build_query_node(operator, children, search_field)

    def _build_query_node(
        self, operator: str, children: List[Union[str, Query]], search_field: str
    ) -> None:
        """parse the query provided, build nodes&tree structure"""
        assert operator in ["AND", "OR", "NOT"]
        self.query_node = Node(operator, True, search_field)
        for item in children:
            if isinstance(item, str):
                term_node = Node(item, False, search_field)
                self.query_node.children.append(term_node)
            elif isinstance(item, Query):
                self.query_node.children.append(item.query_node)
            else:
                raise ValueError("Invalid search term")

        # Mark nodes to prevent circular references
        self.query_node.mark()
        # Remove marks
        self.query_node.remove_marks()

    def write(
        self, file_name: str, *, syntax: str, replace_existing: bool = False
    ) -> None:
        """writes the query to a file"""

        if Path(file_name).exists() and not replace_existing:
            raise FileExistsError("File already exists")
        Path(file_name).parent.mkdir(parents=True, exist_ok=True)

        if syntax == "wos":
            self._write_wos(Path(file_name))
        elif syntax == "pubmed":
            self._write_pubmed(Path(file_name))
        elif syntax == "ieee":
            self._write_ieee(Path(file_name))
        else:
            raise ValueError(f"Syntax not supported ({syntax})")

    def to_string(self, syntax: str = "pre_notation") -> str:
        """prints the query in the selected syntax"""
        if syntax == "pre_notation":
            return self._print_query_pre_notation()
        if syntax == "wos":
            return self._print_query_wos()
        if syntax == "pubmed":
            return self._print_query_pubmed()
        if syntax == "ieee":
            return self._print_query_ieee()
        raise ValueError(f"Syntax not supported ({syntax})")

    def _print_query_pre_notation(self, node: Optional[Node] = None) -> str:
        """prints query in PreNotation"""
        # start node case
        if node is None:
            node = self.query_node

        result = ""
        result = f"{result}{node.value}"
        if node.children == []:
            return result

        result = f"{result}["
        for child in node.children:
            result = f"{result}{self._print_query_pre_notation(child)}"
            if child != node.children[-1]:
                result = f"{result}, "
        return f"{result}]"

    def _write_wos(self, file_name: Path) -> None:
        """translating method for Web of Science database
        creates a JSON file with translation information
        """
        data = {
            "database": "Web of Science - Core Collection",
            "url": "https://www.webofscience.com/wos/woscc/advanced-search",
            "translatedQuery": f"{self.to_string(syntax='wos')}",
            "annotations": (
                "Paste the translated string without quotation marks "
                "into the advanced search free text field."
            ),
        }

        json_object = json.dumps(data, indent=4)

        with open(file_name, "w", encoding="utf-8") as file:
            file.write(json_object)

    def _print_query_wos(self, node: Optional[Node] = None) -> str:
        """actual translation logic for WoS"""
        # start node case
        if node is None:
            node = self.query_node
        result = ""
        for child in node.children:
            if not child.operator:
                # node is not an operator
                if (child == node.children[0]) & (child != node.children[-1]):
                    # current element is first but not only child element
                    # -->operator does not need to be appended again
                    result = (
                        f"{result}"
                        f"{self.get_search_field_wos(child.search_field)}="
                        f"({child.value}"
                    )

                else:
                    # current element is not first child
                    result = f"{result} {node.value} {child.value}"

                if child == node.children[-1]:
                    # current Element is last Element -> closing parenthesis
                    result = f"{result})"

            else:
                # node is operator node
                if child.value == "NOT":
                    # current element is NOT Operator -> no parenthesis in WoS
                    result = f"{result}{self._print_query_wos(child)}"

                elif (child == node.children[0]) & (child != node.children[-1]):
                    result = f"{result}({self._print_query_wos(child)}"
                else:
                    result = f"{result} {node.value} {self._print_query_wos(child)}"

                if (child == node.children[-1]) & (child.value != "NOT"):
                    result = f"{result})"
        return f"{result}"

    def _write_ieee(self, file_name: Path) -> None:
        """translating method for IEEE Xplore database
        creates a JSON file with translation information
        """
        data = {
            "database": "IEEE Xplore",
            "url": "https://ieeexplore.ieee.org/search/advanced/command",
            "translatedQuery": f"{self.to_string(syntax='ieee')}",
            "annotations": (
                "Paste the translated string "
                "without quotation marks into the command search free text field."
            ),
        }

        json_object = json.dumps(data, indent=4)

        with open(file_name, "w", encoding="utf-8") as file:
            file.write(json_object)

    def _print_query_ieee(self, node: Optional[Node] = None) -> str:
        """actual translation logic for IEEE"""
        # start node case
        if node is None:
            node = self.query_node
        result = ""
        for index, child in enumerate(node.children):
            # node is not an operator
            if not child.operator:
                # current element is first but not only child element
                # --> operator does not need to be appended again
                if (child == node.children[0]) & (child != node.children[-1]):
                    result = f'{result}("{child.search_field}":{child.value}'
                    if node.children[index + 1].operator:
                        result = f"({result})"

                else:
                    # current element is not first child
                    result = (
                        f'{result} {node.value} "{child.search_field}":{child.value}'
                    )
                    if child != node.children[-1]:
                        if node.children[index + 1].operator:
                            result = f"({result})"

                if child == node.children[-1]:
                    # current element is last Element -> closing parenthesis
                    result = f"{result})"

            else:
                # node is operator Node
                if (child == node.children[0]) & (child != node.children[-1]):
                    # current Element is OR/AND operator:
                    result = f"{result}{self._print_query_ieee(child)}"
                else:
                    result = f"{result} {node.value} {self._print_query_ieee(child)}"

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

    def _write_pubmed(self, file_name: Path) -> None:
        """translating method for PubMed database
        creates a JSON file with translation information
        """
        data = {
            "database": "PubMed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/advanced/",
            "translatedQuery": f"{self.to_string(syntax='pubmed')}",
            "annotations": (
                "Paste the translated string without quotation marks "
                'into the "Query Box" free text field.'
            ),
        }

        json_object = json.dumps(data, indent=4)

        with open(file_name, "w", encoding="utf-8") as file:
            file.write(json_object)

    def _print_query_pubmed(self, node: Optional[Node] = None) -> str:
        """actual translation logic for PubMed"""
        # start node case
        if node is None:
            node = self.query_node

        result = ""
        for child in node.children:
            if not child.operator:
                # node is not an operator
                if (child == node.children[0]) & (child != node.children[-1]):
                    # current element is first but not only child element
                    # -->operator does not need to be appended again
                    result = (
                        f"{result}({child.value}"
                        f"[{self.get_search_field_pubmed(child.search_field)}]"
                    )

                else:
                    # current element is not first child
                    result = (
                        f"{result} {node.value} {child.value}"
                        f"[{self.get_search_field_pubmed(child.search_field)}]"
                    )

                if child == node.children[-1]:
                    # current Element is last Element -> closing parenthesis
                    result = f"{result})"

            else:
                # node is operator node
                if child.value == "NOT":
                    # current element is NOT Operator -> no parenthesis in PubMed
                    result = f"{result}{self._print_query_pubmed(child)}"

                elif (child == node.children[0]) & (child != node.children[-1]):
                    result = f"{result}({self._print_query_pubmed(child)}"
                else:
                    result = f"{result} {node.value} {self._print_query_pubmed(child)}"

                if (child == node.children[-1]) & (child.value != "NOT"):
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
