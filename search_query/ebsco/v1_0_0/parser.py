"""Versioned EBSCO parser wrappers."""

from __future__ import annotations

from search_query.constants import QueryErrorCode
from search_query.ebsco.parser import EBSCOListParser, EBSCOParser
from search_query.ebsco.linter import EBSCOListLinter
from search_query.query import Query


class EBSCOParser_v1_0_0(EBSCOParser):
    SOURCE = "ebsco"
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


class EBSCOListParser_v1_0_0(EBSCOListParser):
    SOURCE = "ebsco"
    VERSION = "1.0.0"

    def __init__(self, query_list: str, *, field_general: str = "") -> None:
        super().__init__(query_list=query_list, field_general=field_general)
        self.parser_class = EBSCOParser_v1_0_0
        self.linter = EBSCOListLinter(self, EBSCOParser_v1_0_0)

