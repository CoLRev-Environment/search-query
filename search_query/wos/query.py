#!/usr/bin/env python3
"""WOSQuery class."""
import typing

from search_query.query import Query
from search_query.query import SearchField
from search_query.wos.linter import WOSQueryStringLinter


class WOSQuery(Query):
    """WOSQuery class."""

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
        platform: str = "wos",
        validate_on_init: bool = True,
    ) -> None:
        self._children: typing.List[Query] = []
        super().__init__(
            value,
            operator=operator,
            search_field=search_field,
            children=children,
            position=position,
            distance=distance,
            platform="wos",
        )

        if validate_on_init:
            self._run_linter()

    def _run_linter(self) -> None:
        linter = WOSQueryStringLinter()
        linter.validate_query_tree(self)
        linter.check_status()
