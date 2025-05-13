#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import copy
import re
import typing

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.ebsco.serializer import to_string_ebsco
from search_query.pubmed.serializer import to_string_pubmed
from search_query.serializer_generic import to_string_generic
from search_query.serializer_structured import to_string_structured
from search_query.wos.serializer import to_string_wos


# pylint: disable=too-few-public-methods


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

    def copy(self) -> SearchField:
        """Return a copy of the SearchField instance."""
        return SearchField(self.value, position=self.position)


# pylint: disable=too-many-instance-attributes
class Query:
    """Query class."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        value: str,
        *,
        operator: bool = True,
        search_field: typing.Optional[SearchField] = None,
        children: typing.Optional[typing.List[typing.Union[str, Query]]] = None,
        position: typing.Optional[tuple] = None,
        distance: typing.Optional[int] = None,
    ) -> None:
        self._value: str = ""
        self._operator = False
        self._distance = -1
        self._children: typing.List[Query] = []
        self._search_field = None

        self.operator = operator
        self.value = value
        self.distance = distance
        self.search_field = search_field
        self.position = position
        self.marked = False

        # Note: origin_platform is only set for root nodes
        self.origin_platform = ""

        if children:
            for child in children:
                self.add_child(child)

        self._ensure_children_not_circular()

    def copy(self) -> Query:
        """Return a copy of the Query instance."""
        return copy.deepcopy(self)

    @property
    def value(self) -> str:
        """Value property."""
        return self._value

    @value.setter
    def value(self, v: str) -> None:
        """Set value property."""
        if not isinstance(v, str):
            raise TypeError("value must be a string")
        if self.operator and v not in [
            Operators.AND,
            Operators.OR,
            Operators.NOT,
            Operators.NEAR,
            Operators.WITHIN,
            "NOT_INITIALIZED",
        ]:
            raise ValueError(f"Invalid operator value: {v}")
        self._value = v

    @property
    def operator(self) -> bool:
        """Operator property."""
        return self._operator

    @operator.setter
    def operator(self, is_op: bool) -> None:
        """Set operator property."""
        if not isinstance(is_op, bool):
            raise TypeError("operator must be a boolean")
        self._operator = is_op

    @property
    def distance(self) -> typing.Optional[int]:
        """Distance property."""
        return self._distance

    @distance.setter
    def distance(self, dist: typing.Optional[int]) -> None:
        """Set distance property."""
        if not dist:
            return
        if self.operator and self.value in {Operators.NEAR, Operators.WITHIN}:
            if dist is None:
                raise ValueError(f"{self.value} operator requires a distance")
        else:
            if dist is not None:
                raise ValueError(f"{self.value} operator cannot have a distance")
        self._distance = dist

    @property
    def children(self) -> typing.List[Query]:
        """Children property."""
        return self._children

    @children.setter
    def children(self, children: typing.List[Query]) -> None:
        """Set children property."""
        if not isinstance(children, list):
            raise TypeError("children must be a list of Query objects")
        self._children = children

    def add_child(self, child: typing.Union[str, Query]) -> None:
        """Add child to the query."""
        if isinstance(child, str):
            self._children.append(Term(child, search_field=self.search_field))
        elif isinstance(child, Query):
            self._children.append(child)
        else:
            raise TypeError("Children must be Query objects or strings")

    @property
    def search_field(self) -> typing.Optional[SearchField]:
        """Search field property."""
        return self._search_field

    @search_field.setter
    def search_field(self, sf: typing.Optional[SearchField]) -> None:
        """Set search field property."""
        self._search_field = copy.deepcopy(sf) if sf else None

    def selects(self, *, record_dict: dict) -> bool:
        """Indicates whether the query selects a given record."""

        if self.value == Operators.NOT:
            return not self.children[0].selects(record_dict=record_dict)

        if self.value == Operators.AND:
            return all(x.selects(record_dict=record_dict) for x in self.children)

        if self.value == Operators.OR:
            return any(x.selects(record_dict=record_dict) for x in self.children)

        assert not self.operator

        if self.search_field is None:
            raise ValueError("Search field not set")

        if self.search_field.value == Fields.TITLE:
            field_value = record_dict.get("title", "").lower()
        elif self.search_field.value == Fields.ABSTRACT:
            field_value = record_dict.get("abstract", "").lower()
        else:
            raise ValueError(f"Invalid search field: {self.search_field}")

        value = self.value.lower().lstrip('"').rstrip('"')

        # Handle wildcards
        if "*" in value:
            pattern = re.compile(value.replace("*", ".*").lower())
            match = pattern.search(field_value)
            return match is not None

        # Match exact word
        return value.lower() in field_value

    def _get_confusion_matrix(self, records_dict: dict) -> dict:
        relevant_ids = set()
        irrelevant_ids = set()
        selected_ids = set()

        for record_id, record in records_dict.items():
            status = record.get("colrev_status")
            if status == "rev_included":
                relevant_ids.add(record_id)
            elif status in {"rev_excluded", "rev_prescreen_excluded"}:
                irrelevant_ids.add(record_id)

            if self.selects(record_dict=record):
                selected_ids.add(record_id)

        # Only evaluate against relevant + irrelevant records
        eval_ids = relevant_ids | irrelevant_ids
        selected_eval_ids = selected_ids & eval_ids

        true_positives = len(selected_eval_ids & relevant_ids)
        false_positives = len(selected_eval_ids & irrelevant_ids)
        false_negatives = len(relevant_ids - selected_ids)

        return {
            "total_evaluated": len(eval_ids),
            "selected": len(selected_eval_ids),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
        }

    def evaluate(self, records_dict: dict) -> dict:
        """Evaluate the query against records using colrev_status labels.

        - rev_included: relevant
        - rev_excluded / rev_prescreen_excluded: irrelevant
        - others: ignored
        """

        results = self._get_confusion_matrix(records_dict)

        precision = (
            results["true_positives"]
            / (results["true_positives"] + results["false_positives"])
            if (results["true_positives"] + results["false_positives"]) > 0
            else 0
        )
        recall = (
            results["true_positives"]
            / (results["true_positives"] + results["false_negatives"])
            if (results["true_positives"] + results["false_negatives"]) > 0
            else 0
        )
        f1 = (
            (2 * precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        results["precision"] = precision
        results["recall"] = recall
        results["f1_score"] = f1

        return results

    def is_operator(self) -> bool:
        """Check whether the SearchQuery is an operator."""
        return self.operator

    def is_term(self) -> bool:
        """Check whether the SearchQuery is a term."""
        return not self.is_operator()

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

    def to_structured_string(self) -> str:
        """Prints the query in generic syntax"""
        return to_string_structured(self)

    def to_generic_string(self) -> str:
        """Prints the query in generic syntax"""
        return to_string_generic(self)

    def to_string(self) -> str:
        """Prints the query as a string"""

        assert self.origin_platform != ""

        if self.origin_platform == PLATFORM.WOS.value:
            return to_string_wos(self)
        if self.origin_platform == PLATFORM.PUBMED.value:
            return to_string_pubmed(self)
        if self.origin_platform == PLATFORM.EBSCO.value:
            return to_string_ebsco(self)

        raise ValueError(f"Syntax not supported ({self.origin_platform})")

    def translate(self, target_syntax: str, *, search_field_general: str = "") -> Query:
        """Translate the query to the target syntax using the provided translator."""
        # possible extension: inject custom parser:
        # parser: QueryStringParser | None = None

        # pylint: disable=import-outside-toplevel
        from search_query.pubmed.translator import PubmedTranslator
        from search_query.ebsco.translator import EBSCOTranslator
        from search_query.wos.translator import WOSTranslator

        # If the target syntax is the same as the origin, no translation is needed
        if target_syntax == self.origin_platform:
            return self

        if self.origin_platform == "generic":
            generic_query = self.copy()
        else:
            if self.origin_platform == "pubmed":
                pubmed_translator = PubmedTranslator()
                generic_query = pubmed_translator.to_generic_syntax(
                    self, search_field_general=search_field_general
                )
            elif self.origin_platform == "ebsco":
                ebsco_translator = EBSCOTranslator()
                generic_query = ebsco_translator.to_generic_syntax(
                    self, search_field_general=search_field_general
                )
            elif self.origin_platform == "wos":
                wos_translator = WOSTranslator()
                generic_query = wos_translator.to_generic_syntax(
                    self, search_field_general=search_field_general
                )
            else:
                raise NotImplementedError(
                    f"Translation from {self.origin_platform} "
                    "to generic is not implemented"
                )

        if target_syntax == "generic":
            generic_query.origin_platform = target_syntax
            return generic_query
        if target_syntax == "pubmed":
            target_query = PubmedTranslator.to_specific_syntax(generic_query)
            target_query.origin_platform = target_syntax
            return target_query
        if target_syntax == "ebscohost":
            target_query = EBSCOTranslator.to_specific_syntax(generic_query)
            target_query.origin_platform = target_syntax
            return target_query
        if target_syntax == "wos":
            target_query = WOSTranslator.to_specific_syntax(generic_query)
            target_query.origin_platform = target_syntax
            return target_query

        raise NotImplementedError(f"Translation to {target_syntax} is not implemented")


class Term(Query):
    """Term"""

    def __init__(
        self,
        value: str,
        *,
        search_field: typing.Optional[SearchField],
        position: typing.Optional[tuple] = None,
    ) -> None:
        super().__init__(
            value=value,
            operator=False,
            children=None,
            search_field=search_field,
            position=position,
        )
