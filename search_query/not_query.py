#!/usr/bin/env python
"""NOT Query"""
from typing import List

from search_query.query import Query


class NotQuery(Query):
    """NOT Query"""

    def __init__(
        self, search_terms: List[str], nested_queries: List[Query], search_field: str
    ):
        """init method
        search terms: strings which you want to include in the search query
        nested queries: queries whose roots are appended to the query
        search field: search field to which the query should be applied
        options: Author Keywords, Abstract, Author, DOI, ISBN, Publisher or Title
        """

        super().__init__(
            operator="NOT",
            search_terms=search_terms,
            nested_queries=nested_queries,
            search_field=search_field,
        )
