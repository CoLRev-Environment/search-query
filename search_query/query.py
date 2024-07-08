#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import json
import textwrap
import typing
from abc import ABC
from pathlib import Path

from search_query.constants import Colors
from search_query.constants import Fields
from search_query.constants import Operators
from search_query.serializer_pubmed import to_string_pubmed

# pylint: disable=too-few-public-methods


def reindent(input_str: str, num_spaces: int) -> str:
    """Reindents the input string by num_spaces spaces."""
    lines = textwrap.wrap(input_str, 100, break_long_words=False)
    prefix = num_spaces * 3 * " "
    if num_spaces >= 1:
        prefix = "|" + num_spaces * 3 * " "
    lines = [prefix + line for line in lines]
    if num_spaces == 1:
        lines[0] = lines[0].replace(prefix, "|---")
    return "\n".join(lines)


class SearchField:
    """SearchField class."""

    def __init__(
        self,
        value: str,
        *,
        position: typing.Optional[tuple] = None,
    ) -> None:
        """init method"""
        self.value = value
        self.position = position

    def __str__(self) -> str:
        return self.value


class Query(ABC):
    """Query class."""

    # pylint: disable=too-many-arguments
    # @abstractmethod
    def __init__(
        self,
        value: str = "NOT_INITIALIZED",
        *,
        operator: bool = False,
        search_field: typing.Optional[SearchField] = None,
        children: typing.Optional[typing.List[typing.Union[str, Query]]] = None,
        position: typing.Optional[tuple] = None,
        color: str = "",
    ) -> None:
        """init method - abstract"""

        self.value = value
        self.operator = operator
        if operator:
            assert value in [
                Operators.AND,
                Operators.OR,
                Operators.NOT,
                "NOT_INITIALIZED",
            ]

        self.children: typing.List[Query] = []
        if children:
            for child in children:
                if isinstance(child, str):
                    self.children.append(
                        Query(child, operator=False, search_field=search_field)
                    )
                else:
                    self.children.append(child)

        self.marked = False
        self.search_field = search_field
        if operator:
            self.search_field = None
        self.position = position
        self.color = color

        self._ensure_children_not_circular()

    def get_nr_leaves(self) -> int:
        """Returns the number of leaves in the query tree"""
        return self._get_nr_leaves_from_node(self)

    def _get_nr_leaves_from_node(self, node: Query) -> int:
        return sum(
            self._get_nr_leaves_from_node(n) if n.operator else 1 for n in node.children
        )

    def _ensure_children_not_circular(
        self,
    ) -> None:
        """parse the query provided, build nodes&tree structure"""

        # Mark nodes to prevent circular references
        self.mark()
        # Remove marks
        self.remove_marks()

    def mark(self) -> None:
        """marks the node"""
        if self.marked:
            raise ValueError("Building Query Tree failed")
        self.marked = True
        for child in self.children:
            child.mark()

    def remove_marks(self) -> None:
        """removes the mark from the node"""
        self.marked = False
        for child in self.children:
            child.remove_marks()

    def print_node(self) -> str:
        """returns a string with all information to the node"""
        return (
            f"value: {self.value} "
            f"operator: {str(self.operator)} "
            f"search field: {self.search_field}"
        )

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
        if syntax == "structured":
            return self._print_query_structured()
        if syntax == "wos":
            return self._print_query_wos()
        if syntax == "pubmed":
            return to_string_pubmed(self)
        if syntax == "ieee":
            return self._print_query_ieee()
        raise ValueError(f"Syntax not supported ({syntax})")

    def _print_query_pre_notation(self, node: typing.Optional[Query] = None) -> str:
        """prints query in PreNotation"""
        # start node case
        if node is None:
            node = self

        if not hasattr(node, "value"):
            return " (?) "

        result = ""
        node_content = node.value
        if node.search_field:
            node_content += f"[{node.search_field}]"

        if hasattr(node, "near_param"):
            node_content += f"({node.near_param})"
        if node.color:
            result = f"{result}{node.color}{node_content}{Colors.END}"
        else:
            result = f"{result}{node_content}"
        if node.children == []:
            return result

        result = f"{result}["
        for child in node.children:
            result = f"{result}{self._print_query_pre_notation(child)}"
            if child != node.children[-1]:
                result = f"{result}, "
        return f"{result}]"

    def _print_query_structured(
        self, node: typing.Optional[Query] = None, *, level: int = 0
    ) -> str:
        """prints query in structured notation"""
        if node is None:
            node = self

        indent = "   "
        result = ""

        if not hasattr(node, "value"):
            return f"{indent} (?)"

        search_field = ""
        if not node.operator:
            search_field = f"[{node.search_field}]"

        node_value = node.value
        if hasattr(node, "near_param"):
            node_value += f"/{node.near_param}"
        if node.color:
            result = reindent(
                f"{node.color}{node_value} {search_field}{Colors.END}", level
            )
        else:
            result = reindent(f"{node_value} {search_field}", level)

        if node.children == []:
            return result

        result = f"{result}[\n"
        for child in node.children:
            result = (
                f"{result}{self._print_query_structured(child, level = level +1 )}\n"
            )
        result = f"{result}{'|' + ' ' *level*3 + ' '}]"

        return result

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

    def _print_query_wos(self, node: typing.Optional[Query] = None) -> str:
        """actual translation logic for WoS"""
        # start node case
        if node is None:
            node = self
        result = ""
        for child in node.children:
            if not child.operator:
                # node is not an operator
                if (child == node.children[0]) & (child != node.children[-1]):
                    # current element is first but not only child element
                    # -->operator does not need to be appended again
                    result = (
                        f"{result}"
                        f"{self._get_search_field_wos(str(child.search_field))}="
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

    # https://ieeexplore.ieee.org/Xplorehelp/searching-ieee-xplore/command-search
    def _translate_search_field_ieee(self, search_field: str) -> str:
        """transform search field to IEEE Syntax"""
        if search_field == Fields.AUTHOR_KEYWORDS:
            result = "Author Keywords"
        elif search_field == Fields.ABSTRACT:
            result = "Abstract"
        elif search_field == Fields.AUTHOR:
            result = "Authors"
        elif search_field == Fields.DOI:
            result = "DOI"
        elif search_field == Fields.ISBN_ISSN:
            result = "ISBN"
        elif search_field == Fields.PUBLISHER:
            result = "Publisher"
        elif search_field == Fields.TITLE:
            result = "Title"
        else:
            raise ValueError(f"Search field not supported ({search_field})")
        return result

    def _print_query_ieee(self, node: typing.Optional[Query] = None) -> str:
        """actual translation logic for IEEE"""
        # start node case
        if node is None:
            node = self
        result = ""
        for index, child in enumerate(node.children):
            # node is not an operator
            if not child.operator:
                # current element is first but not only child element
                # --> operator does not need to be appended again
                if (child == node.children[0]) & (child != node.children[-1]):
                    result = (
                        f'{result}("'
                        f'{self._translate_search_field_ieee(str(child.search_field))}"'
                        + f":{child.value}"
                    )
                    if node.children[index + 1].operator:
                        result = f"({result})"

                else:
                    s_field = self._translate_search_field_ieee(str(child.search_field))
                    # current element is not first child
                    result = f'{result} {node.value} "{s_field}":{child.value}'
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

    # https://pubmed.ncbi.nlm.nih.gov/help/
    # https://images.webofknowledge.com/images/help/WOS/hs_advanced_fieldtags.html
    # https://images.webofknowledge.com/images/help/WOS/hs_wos_fieldtags.html
    def _get_search_field_wos(self, search_field: str) -> str:
        """transform search field to WoS Syntax"""
        if search_field == Fields.AUTHOR_KEYWORDS:
            result = "AK"
        elif search_field == Fields.ABSTRACT:
            result = "AB"
        elif search_field == Fields.AUTHOR:
            result = "AU"
        elif search_field == Fields.DOI:
            result = "DO"
        elif search_field == Fields.ISBN_ISSN:
            result = "IS"
        elif search_field == Fields.PUBLISHER:
            result = "PUBL"
        elif search_field == Fields.TITLE:
            result = "TI"
        elif search_field == Fields.DOCUMENT_TYPE:
            result = "DT"
        else:
            raise ValueError(f"Search field not supported ({search_field})")
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


# TODO: extract to serializer
