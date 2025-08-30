"""Versioned Web of Science parser wrappers."""

from __future__ import annotations

from search_query.constants import QueryErrorCode
from search_query.wos.parser import WOSListParser, WOSParser
from search_query.wos.linter import WOSQueryListLinter
from search_query.query import Query


class WOSParser_v1_0_0(WOSParser):
    SOURCE = "wos"
    VERSION = "1.0.0"

    def parse(self) -> Query:  # type: ignore[override]
        query = super().parse()
        if "TIAB" in self.query_str.upper():
            self.linter.add_message(
                QueryErrorCode.LINT_DEPRECATED_SYNTAX,
                details="TIAB field alias",
                fatal=False,
            )
        return query


class WOSListParser_v1_0_0(WOSListParser):
    SOURCE = "wos"
    VERSION = "1.0.0"

    def __init__(self, query_list: str, *, field_general: str = "") -> None:
        super().__init__(query_list=query_list, field_general=field_general)
        self.parser_class = WOSParser_v1_0_0
        self.linter = WOSQueryListLinter(self, WOSParser_v1_0_0)

