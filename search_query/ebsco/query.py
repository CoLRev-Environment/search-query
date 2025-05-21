#!/usr/bin/env python3
"""EBSCOQuery class."""
import typing

from search_query.ebsco.linter import EBSCOQueryStringLinter
from search_query.query import Query
from search_query.query import SearchField


class EBSCOQuery(Query):
    """EBSCOQuery class."""

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
        platform: str = "ebsco",
        validate_on_init: bool = True,
    ) -> None:
        super().__init__(
            value,
            operator=operator,
            search_field=search_field,
            children=children,
            position=position,
            distance=distance,
            platform="ebsco",
        )

        if validate_on_init:
            self._run_linter()

    def _run_linter(self) -> None:
        ebsco_linter = EBSCOQueryStringLinter()
        ebsco_linter.validate_query_tree(self)
        ebsco_linter.check_status()
