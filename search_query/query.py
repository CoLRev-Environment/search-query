#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import copy
import re
import typing

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import SearchField
from search_query.ebsco.serializer import to_string_ebsco
from search_query.generic.serializer import to_string_generic
from search_query.pubmed.serializer import to_string_pubmed
from search_query.serializer_structured import to_string_structured
from search_query.wos.serializer import to_string_wos


# pylint: disable=too-many-public-methods
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
        platform: str = "generic",
    ) -> None:
        self._value: str = ""
        self._operator = False
        self._distance = None
        self._children: typing.List[Query] = []
        self._search_field = None

        self.operator = operator
        self.value = value
        self.distance = distance
        if isinstance(search_field, str):
            self.search_field = SearchField(search_field)
        else:
            self.search_field = search_field
        self.position = position
        self.marked = False
        # Note: platform is only set for root nodes
        self._platform = platform
        # helper flag to silence linter after parse() to avoid repeated linter printout
        self._silence_linter = False

        self._parent: typing.Optional[Query] = None
        if children:
            for child in children:
                self.add_child(child)

        self._set_platform_recursively(platform)

        self._ensure_children_not_circular()

        # Note: validating platform constraints is particularly important
        # when queries are created programmatically
        self._validate_platform_constraints()

    def _validate_platform_constraints(self) -> None:
        if self.platform == "deactivated":
            return

        # pylint: disable=import-outside-toplevel
        if self.platform == PLATFORM.WOS.value:
            from search_query.wos.linter import WOSQueryStringLinter

            wos_linter = WOSQueryStringLinter()
            wos_linter.validate_query_tree(self)
            if not self._silence_linter:
                wos_linter.check_status()

        elif self.platform == PLATFORM.PUBMED.value:
            from search_query.pubmed.linter import PubmedQueryStringLinter

            pubmed_linter = PubmedQueryStringLinter()
            pubmed_linter.validate_query_tree(self)
            if not self._silence_linter:
                pubmed_linter.check_status()

        elif self.platform == "generic":
            from search_query.generic.linter import GenericLinter

            gen_linter = GenericLinter()
            gen_linter.validate_query_tree(self)
            if not self._silence_linter:
                gen_linter.check_status()

        elif self.platform == PLATFORM.EBSCO.value:
            from search_query.ebsco.linter import EBSCOQueryStringLinter

            ebsco_linter = EBSCOQueryStringLinter()
            ebsco_linter.validate_query_tree(self)
            if not self._silence_linter:
                ebsco_linter.check_status()

        else:  # pragma: no cover
            raise NotImplementedError(
                f"Validation for {self.platform} is not implemented"
            )

    def _set_platform_recursively(self, platform: str) -> None:
        """Set the origin platform for this query node and its children."""
        self._platform = platform
        for child in self._children:
            # pylint: disable=protected-access
            child._set_platform_recursively(platform)

    @property
    def platform(self) -> str:
        """Platform property."""
        return self._platform

    @platform.setter
    def platform(self, platform: str) -> None:
        """Set the platform property."""
        if platform not in [p.value for p in PLATFORM] + ["deactivated"]:
            raise ValueError(f"Invalid platform: {platform}")
        self._set_platform_recursively(platform)
        self._validate_platform_constraints()

    def set_platform_unchecked(self, platform: str, silent: bool = False) -> None:
        """Set the platform for this query node without validation.
        This is an optional utility for parsers.
        """

        if silent:
            self._silence_linter = True
        self._set_platform_recursively(platform)

    def __deepcopy__(self, memo: dict) -> Query:
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        for k, v in self.__dict__.items():
            if k == "_parent":
                setattr(
                    result, k, None
                )  # parent will be reset manually during tree reconstruction
            else:
                setattr(result, k, copy.deepcopy(v, memo))

        return result

    def _reset_parent_links(self) -> None:
        """Reset parent pointers after deepcopy to restore correct tree structure."""
        for child in self.children:
            child._parent = self  # pylint: disable=protected-access
            child._reset_parent_links()  # pylint: disable=protected-access

    def copy(self) -> Query:
        """Return a deep copy of the Query instance without parent references."""
        copied = copy.deepcopy(self, memo={})
        copied._reset_parent_links()  # pylint: disable=protected-access
        return copied

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
            Operators.RANGE,
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
        """Set the children of the query, updating parent pointers."""
        # Clear existing children and reset parent links (if necessary)
        self._children.clear()
        if not isinstance(children, list):
            raise TypeError("children must be a list of Query instances or strings")

        # Note: OrQuery, AndQuery, NearQuery, NotQuery, RANGEQuery offeride the setter
        # with specific validation.

        # Add each new child using add_child (ensures parent is set)
        for child in children or []:
            self.add_child(child)

    def add_child(self, child: typing.Union[str, Query]) -> Query:
        """Add a child Query node and set its parent pointer."""
        if isinstance(child, str):
            # pylint: disable=import-outside-toplevel
            from search_query.query_term import Term

            child = Term(
                child,
                search_field=self.search_field,
                platform=self.platform,
            )
        if not isinstance(child, Query):
            raise TypeError("Child must be a Query instance or a string")
        child._set_parent(self)  # pylint: disable=protected-access
        self._children.append(child)
        return child

    def _set_parent(self, parent: typing.Optional[Query]) -> None:
        """Internal method to update the parent of this node."""
        self._parent = parent

    def get_parent(self) -> typing.Optional[Query]:
        """Return the parent Query node, or None if this node is the root."""
        return self._parent

    def get_root(self) -> Query:
        """Return the root of the query tree by climbing up parent pointers."""
        return self if self._parent is None else self._parent.get_root()

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
        # pylint: disable=import-outside-toplevel
        from search_query.translator_base import QueryTranslator

        query_with_term_fields = self.copy()
        QueryTranslator.move_fields_to_terms(query_with_term_fields)

        # pylint: disable=protected-access
        return query_with_term_fields._selects(record_dict=record_dict)

    def _selects(self, record_dict: dict) -> bool:
        if self.value == Operators.NOT:
            return not self.children[0].selects(record_dict=record_dict)

        if self.value == Operators.AND:
            return all(x.selects(record_dict=record_dict) for x in self.children)

        if self.value == Operators.OR:
            return any(x.selects(record_dict=record_dict) for x in self.children)

        assert not self.operator

        assert self.search_field is not None, "Search field must be set for terms"
        if self.search_field.value == Fields.TITLE:
            field_value = record_dict.get("title", "").lower()
        elif self.search_field.value == Fields.ABSTRACT:
            field_value = record_dict.get("abstract", "").lower()
        else:
            raise ValueError(f"Unsupported search field: {self.search_field}")

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

    def is_term(self) -> bool:
        """Check whether the SearchQuery is a term."""
        return not self.operator

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
        self._mark()
        # Remove marks
        self._remove_marks()

    def _mark(self) -> None:
        """marks the node"""
        if self.marked:
            raise ValueError("Building Query Tree failed")
        self.marked = True
        for child in self.children:
            # pylint: disable=protected-access
            child._mark()

    def _remove_marks(self) -> None:
        """removes the mark from the node"""
        self.marked = False
        for child in self.children:
            # pylint: disable=protected-access
            child._remove_marks()

    def to_structured_string(self) -> str:
        """Prints the query in generic syntax"""
        return to_string_structured(self)

    def to_generic_string(self) -> str:
        """Prints the query in generic syntax"""
        return to_string_generic(self)

    def to_string(self) -> str:
        """Prints the query as a string"""

        assert self.platform != ""

        if self.platform == PLATFORM.WOS.value:
            return to_string_wos(self)
        if self.platform == PLATFORM.PUBMED.value:
            return to_string_pubmed(self)
        if self.platform == PLATFORM.EBSCO.value:
            return to_string_ebsco(self)

        raise ValueError(f"Syntax not supported ({self.platform})")  # pragma: no cover

    def translate(self, target_syntax: str) -> Query:
        """Translate the query to the target syntax using the provided translator."""
        # possible extension: inject custom parser:
        # parser: QueryStringParser | None = None

        # pylint: disable=import-outside-toplevel
        from search_query.pubmed.translator import PubmedTranslator
        from search_query.ebsco.translator import EBSCOTranslator
        from search_query.wos.translator import WOSTranslator

        # If the target syntax is the same as the origin, no translation is needed
        if target_syntax == self.platform:
            return self

        if self.platform == "generic":
            generic_query = self.copy()
        else:
            if self.platform == PLATFORM.PUBMED.value:
                pubmed_translator = PubmedTranslator()
                generic_query = pubmed_translator.to_generic_syntax(self)
            elif self.platform == PLATFORM.EBSCO.value:
                ebsco_translator = EBSCOTranslator()
                generic_query = ebsco_translator.to_generic_syntax(self)
            elif self.platform == PLATFORM.WOS.value:
                wos_translator = WOSTranslator()
                generic_query = wos_translator.to_generic_syntax(self)
            else:  # pragma: no cover
                raise NotImplementedError(
                    f"Translation from {self.platform} " "to generic is not implemented"
                )

        if target_syntax == "generic":
            generic_query.platform = target_syntax
            return generic_query
        if target_syntax == PLATFORM.PUBMED.value:
            target_query = PubmedTranslator.to_specific_syntax(generic_query)
            target_query.platform = target_syntax
            return target_query
        if target_syntax == PLATFORM.EBSCO.value:
            target_query = EBSCOTranslator.to_specific_syntax(generic_query)
            target_query.platform = target_syntax
            return target_query
        if target_syntax == PLATFORM.WOS.value:
            target_query = WOSTranslator.to_specific_syntax(generic_query)
            target_query.platform = target_syntax
            return target_query

        raise NotImplementedError(
            f"Translation to {target_syntax} is not implemented"
        )  # pragma: no cover
