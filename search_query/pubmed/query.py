#!/usr/bin/env python3
"""PUBMEDQuery class."""
import typing

from search_query.pubmed.linter import PubmedQueryStringLinter
from search_query.query import Query
from search_query.query import SearchField


class PUBMEDQuery(Query):
    """PUBMEDQuery class."""

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
        platform: str = "pubmed",
        validate_on_init: bool = True,
    ) -> None:
        super().__init__(
            value,
            operator=operator,
            search_field=search_field,
            children=children,
            position=position,
            distance=distance,
            platform="pubmed",
        )
        if validate_on_init:
            self._run_linter()

    def _run_linter(self) -> None:
        pubmed_linter = PubmedQueryStringLinter()
        pubmed_linter.validate_query_tree(self)
        pubmed_linter.check_status()
