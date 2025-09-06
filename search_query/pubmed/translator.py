#!/usr/bin/env python3
"""Pubmed query translator."""
from __future__ import annotations

import typing
from collections import defaultdict
from itertools import permutations

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.pubmed.constants import generic_field_to_syntax_field
from search_query.pubmed.constants import syntax_str_to_generic_field_set
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_near import NEARQuery
from search_query.query_or import OrQuery
from search_query.query_term import Term
from search_query.translator_base import QueryTranslator


class PubmedTranslator(QueryTranslator):
    """Translator for Pubmed queries."""

    @classmethod
    def _expand_flat_or_chains(cls, query: Query) -> bool:
        """Expand flat OR chains into a single OR query."""

        if not (query.operator and query.value == Operators.OR):
            return False
        if not all(not child.operator for child in query.children):
            return False
        assert all(child.field for child in query.children)

        fields = {child.field.value for child in query.children if child.field}

        if len(fields) != 1:
            return False

        if next(iter(fields)) in {"[title and abstract]", "[tiab]"}:
            existing_children = list(query.children)
            for child in existing_children:
                if not child.field:  # pragma: no cover
                    continue
                child.field.value = Fields.TITLE
                new_child = Term(
                    value=child.value,
                    field=SearchField(value=Fields.ABSTRACT),
                )
                query.add_child(new_child)

            return True

        # elif ... other cases?

        return False  # pragma: no cover

    @classmethod
    def _translate_fields(cls, query: Query) -> None:
        if query.operator:
            for child in query.children:
                cls._translate_fields(child)

        else:
            if query.field and query.field.value not in ["[tiab]"]:
                query.field.value = generic_field_to_syntax_field(query.field.value)

    @classmethod
    def _combine_tiab(cls, query: Query) -> None:
        """Recursively combine identical terms from TI and AB into TIAB."""

        if query.operator and query.value == "OR":
            # ab does not exist: always expand to tiab
            terms = []
            for child in query.children:
                if not child.operator and child.field and child.field.value == "ab":
                    child.field.value = "[tiab]"
                    terms.append(child.value)

            if terms:
                print(f"Info: combining terms from AB OR TI to TIAB: {terms}")

            # Warn if the same terms are not available with ti
            missing_terms = []
            for term in terms:
                if not any(
                    term == child.value and child.field and child.field.value == "ti"
                    for child in query.children
                ):
                    missing_terms.append(term)
            if missing_terms:
                print(
                    "Info/Warning: Search field broadened for term "
                    "(AB "
                    "(without corresponding search for the same term with TI)"
                    " -> TIAB): "
                    f"{missing_terms}"
                )

            # Remove duplicates with ti
            new_children = []
            for child in query.children:
                if child.operator:
                    # unconditionally append operators
                    new_children.append(child)
                elif child.field and not (
                    child.field.value == "ti" and child.value in terms
                ):
                    new_children.append(child)
            query.children = new_children

        # Recursively apply to child queries
        for child in query.children:
            cls._combine_tiab(child)

    # pylint: disable=too-many-locals, too-many-branches
    @classmethod
    def _collapse_near_queries(cls, query: Query) -> Query:
        """Recursively collapse NEAR queries in the query tree."""
        if not query.children:
            return query

        if query.value == Operators.NEAR:
            query.children[
                0
            ].value = f'"{query.children[0].value} {query.children[1].value}"'
            query.children.pop()
            return query

        if query.value == Operators.OR:
            # Extract NEAR queries
            near_queries: typing.List[Query] = []
            other_queries: typing.List[Query] = []
            for child in query.children:
                # pylint: disable=unidiomatic-typecheck
                (near_queries if type(child) is NEARQuery else other_queries).append(
                    child
                )

            for other_query in other_queries:
                cls._collapse_near_queries(other_query)

            # Group NEAR queries by their proximity distance
            grouped_queries = defaultdict(list)
            for near_query in near_queries:
                key = near_query.distance if hasattr(near_query, "distance") else 0
                grouped_queries[key].append(near_query)

            combined_near_queries = []
            for distance, queries in grouped_queries.items():
                # For each group, extract term pairs from NEAR queries and
                # map them to corresponding fields
                term_field_map = defaultdict(set)
                for q in queries:
                    term_a = q.children[0].value
                    term_b = q.children[1].value
                    assert q.children[0].field
                    term_field_map[(min(term_a, term_b), max(term_a, term_b))].add(
                        q.children[0].field.value
                    )

                for (term_a, term_b), fields in term_field_map.items():
                    if Fields.TITLE in fields and Fields.ABSTRACT in fields:
                        # Merge 'Title' and 'Abstract' into '[tiab]' in the mapping
                        fields.add("[tiab]")
                        fields.remove(Fields.TITLE)
                        fields.remove(Fields.ABSTRACT)
                    for field in fields:
                        # Generate NEAR queries from the mapping
                        combined_near_queries.append(
                            NEARQuery(
                                value=Operators.NEAR,
                                children=[
                                    Term(
                                        value=f'"{term_a} {term_b}"',
                                        field=SearchField(value=field),
                                        platform="deactivated",
                                    )
                                ],
                                distance=distance,
                                platform="deactivated",
                            )
                        )

                    # Collapse proximity searches with 3+ terms ?

            query_children = other_queries + combined_near_queries

            if len(query_children) == 1:
                # If only one NEAR query remains, replace the OR query with it
                if not query.get_parent():
                    return query_children.pop()
                query.replace(query_children.pop())
            else:
                query.children = query_children

            return query

        for child in query.children:
            cls._collapse_near_queries(child)

        return query

    @classmethod
    def translate_fields_to_generic(cls, query: Query) -> Query:
        """Translate search fields"""

        if query.children:
            if query.value == Operators.NEAR:
                # Expand NEAR queries
                assert query.children[0].field
                field_set = syntax_str_to_generic_field_set(
                    query.children[0].field.value
                )
                expanded_query = cls._expand_near_query(query, field_set)
                if not query.get_parent():
                    return expanded_query
                query.replace(expanded_query)
            else:
                expanded = cls._expand_flat_or_chains(query)
                if not expanded:
                    for child in query.children:
                        cls.translate_fields_to_generic(child)

        if query.field:
            field_set = syntax_str_to_generic_field_set(query.field.value)
            if len(field_set) == 1:
                query.field.value = field_set.pop()
            else:
                # Convert queries in the form 'Term [tiab]'
                # into 'Term [ti] OR Term [ab]'.
                expanded_query = cls._expand_combined_fields(query, field_set)
                if not query.get_parent():
                    return expanded_query
                query.replace(expanded_query)

        return query

    @classmethod
    def _expand_combined_fields(cls, query: Query, fields: set) -> Query:
        """Expand queries with combined search fields into an OR query"""
        query_children = []
        # Note: PubMed accepts fields only at the level of terms.
        # otherwise, the following would need to cover additional cases.
        # Note: sorted list for deterministic order of fields
        for field in sorted(list(fields)):
            query_children.append(
                Term(
                    value=query.value,
                    field=SearchField(value=field),
                )
            )
        return OrQuery(
            children=query_children,  # type: ignore
            field=None,
        )

    @classmethod
    def _expand_near_query(cls, query: Query, fields: set) -> Query:
        """Expand NEAR query into an OR query"""
        if type(query) is not NEARQuery:  # pylint: disable=unidiomatic-typecheck
            return query
        distance = 0
        if hasattr(query, "distance"):
            distance = int(query.distance)  # type: ignore

        query_children = []
        terms = query.children[0].value.strip('"').split()
        # Handle [tiab] by generating NEAR queries for both 'title' and 'abstract'
        for field in sorted(list(fields)):
            # Get all possible ordered pairs of search terms
            # in the proximity search phrase
            pairs = list(permutations(terms, 2))
            for pair in pairs:
                # Create binary near query for each pair
                query_children.append(
                    NEARQuery(
                        value=Operators.NEAR,
                        children=[
                            Term(
                                value=pair[0],
                                field=SearchField(value=field),
                            ),
                            Term(
                                value=pair[1],
                                field=SearchField(value=field),
                            ),
                        ],
                        distance=distance,
                    )
                )
        return OrQuery(
            children=query_children,  # type: ignore
            field=None,
        )

    @classmethod
    def to_generic_syntax(cls, query: Query) -> Query:
        """Convert the query to a generic syntax."""

        query = query.copy()
        query = cls.translate_fields_to_generic(query)
        return query

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

        query = query.copy()

        cls.move_fields_to_terms(query)
        cls.flatten_nested_operators(query)
        query = cls._collapse_near_queries(query)
        cls._combine_tiab(query)
        cls._translate_fields(query)
        cls._remove_redundant_terms(query)

        return query
