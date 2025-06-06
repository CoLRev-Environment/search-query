#!/usr/bin/env python3
"""Pubmed query translator."""
import itertools

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.pubmed.constants import generic_search_field_to_syntax_field
from search_query.pubmed.constants import syntax_str_to_generic_search_field_set
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_near import NEARQuery
from search_query.query_or import OrQuery
from search_query.query_term import Term
from search_query.translator_base import QueryTranslator


class PubmedTranslator(QueryTranslator):
    """Translator for Pubmed queries."""

    @classmethod
    def _expand_flat_or_chains(cls, query: "Query") -> bool:
        """Expand flat OR chains into a single OR query."""

        if not (query.operator and query.value == Operators.OR):
            return False
        if not all(not child.operator for child in query.children):
            return False
        assert all(child.search_field for child in query.children)

        search_fields = {
            child.search_field.value for child in query.children if child.search_field
        }

        if len(search_fields) != 1:
            return False

        if next(iter(search_fields)) in {"[title and abstract]", "[tiab]"}:
            existing_children = list(query.children)
            for child in existing_children:
                if not child.search_field:  # pragma: no cover
                    continue
                child.search_field.value = Fields.TITLE
                new_child = Term(
                    value=child.value,
                    search_field=SearchField(value=Fields.ABSTRACT),
                )
                query.add_child(new_child)

            return True

        # elif ... other cases?

        return False  # pragma: no cover

    @classmethod
    def _translate_search_fields(cls, query: "Query") -> None:
        if query.operator:
            for child in query.children:
                cls._translate_search_fields(child)

        else:
            if query.search_field and query.search_field.value not in ["[tiab]"]:
                query.search_field.value = generic_search_field_to_syntax_field(
                    query.search_field.value
                )

    @classmethod
    def _combine_tiab(cls, query: "Query") -> None:
        """Recursively combine identical terms from TI and AB into TIAB."""

        if query.operator and query.value == "OR":
            # ab does not exist: always expand to tiab
            terms = []
            for child in query.children:
                if (
                    not child.operator
                    and child.search_field
                    and child.search_field.value == "ab"
                ):
                    child.search_field.value = "[tiab]"
                    terms.append(child.value)

            if terms:
                print(f"Info: combining terms from AB OR TI to TIAB: {terms}")

            # Warn if the same terms are not available with ti
            missing_terms = []
            for term in terms:
                if not any(
                    term == child.value
                    and child.search_field
                    and child.search_field.value == "ti"
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
                elif child.search_field and not (
                    child.search_field.value == "ti" and child.value in terms
                ):
                    new_children.append(child)
            query.children = new_children

        # Recursively apply to child querys
        for child in query.children:
            cls._combine_tiab(child)

    @classmethod
    def translate_search_fields_to_generic(cls, query: Query) -> Query:
        """Translate search fields"""

        if query.children:
            if query.value == Operators.NEAR:
                expanded_query = cls._expand_near_query(query)
                if not query.get_parent():
                    return expanded_query
                query.replace(expanded_query)
            else:
                expanded = cls._expand_flat_or_chains(query)
                if not expanded:
                    for child in query.children:
                        cls.translate_search_fields_to_generic(child)

        if query.search_field:
            search_field_set = syntax_str_to_generic_search_field_set(
                query.search_field.value
            )
            if len(search_field_set) == 1:
                query.search_field.value = search_field_set.pop()
            else:
                # Convert queries in the form 'Term [tiab]'
                # into 'Term [ti] OR Term [ab]'.
                expanded_query = cls._expand_combined_fields(query, search_field_set)
                if not query.get_parent():
                    return expanded_query
                query.replace(expanded_query)

        return query

    @classmethod
    def _expand_combined_fields(cls, query: Query, search_fields: set) -> Query:
        """Expand queries with combined search fields into an OR query"""
        query_children = []
        # Note: PubMed accepts fields only at the level of terms.
        # otherwise, the following would need to cover additional cases.
        # Note: sorted list for deterministic order of fields
        for search_field in sorted(list(search_fields)):
            query_children.append(
                Term(
                    value=query.value,
                    search_field=SearchField(value=search_field),
                )
            )
        return OrQuery(
            children=query_children,
            search_field=None,
        )

    @classmethod
    def _expand_near_query(cls, query: Query) -> Query:
        """Expand NEAR query into an OR query"""
        if type(query) is not NEARQuery:
            return query

        distance = query.distance if hasattr(query, 'distance') else 0
        query_children = []
        search_terms = query.children[0].value.strip('"').split()
        # Handle [tiab] by generating NEAR queries for both 'title' and 'abstract'
        for search_field in sorted(list(syntax_str_to_generic_search_field_set(query.children[0].search_field.value))):
            # Get all possible ordered pairs of search terms in the proximity search phrase
            pairs = list(itertools.permutations(search_terms, 2))
            for pair in pairs:
                # Create binary near query for each pair
                query_children.append(
                    NEARQuery(
                        value=Operators.NEAR,
                        children=[
                            Term(value=pair[0], search_field=SearchField(value=search_field)),
                            Term(value=pair[1], search_field=SearchField(value=search_field)),
                        ],
                        distance=distance
                    )
                )
        return OrQuery(
            children=query_children,
            search_field=None,
        )

    @classmethod
    def to_generic_syntax(cls, query: "Query") -> "Query":
        """Convert the query to a generic syntax."""

        query = query.copy()
        query = cls.translate_search_fields_to_generic(query)
        return query

    @classmethod
    def to_specific_syntax(cls, query: "Query") -> "Query":
        """Convert the query to a specific syntax."""

        query = query.copy()

        cls.move_fields_to_terms(query)
        cls.flatten_nested_operators(query)
        cls._combine_tiab(query)
        cls._translate_search_fields(query)
        cls._remove_redundant_terms(query)

        return query
