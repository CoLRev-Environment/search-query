"""Parse Crossref API URLs into query trees."""
from __future__ import annotations

import typing
from urllib.parse import parse_qsl
from urllib.parse import urlsplit

from search_query.constants import Fields
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import SearchField
from search_query.crossref.linter import CrossrefLinter
from search_query.exception import ListQuerySyntaxError
from search_query.linter_base import QueryListLinter
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query_and import AndQuery
from search_query.query_term import Term

if typing.TYPE_CHECKING:  # pragma: no cover
    from typing import NoReturn


QUERY_FIELDS = {
    "query": Fields.ALL,
    "query.bibliographic": Fields.ALL,
    "query.title": Fields.TITLE,
    "query.author": Fields.AUTHOR,
}
SUPPORTED_PATHS = {"/works"}
SUPPORTED_OPTIONS = {"sort", "order", "filter", "rows", "cursor", "select", "mailto"}


class CrossrefParser(QueryStringParser):
    """Parse the supported Crossref ``/works`` URL format."""

    VERSION = "1"

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        query_str: str,
        *,
        field_general: str = "",
        offset: dict | None = None,
        original_str: str | None = None,
        silent: bool = False,
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_str=query_str,
            field_general=field_general,
            offset=offset,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter = CrossrefLinter(
            query_str=query_str,
            silent=self.silent,
            ignore_failing_linter=self.ignore_failing_linter,
        )

    def _syntax_error(self, details: str) -> NoReturn:
        self.linter.add_message(
            QueryErrorCode.INVALID_SYNTAX,
            positions=[(0, len(self.query_str))],
            details=details,
            fatal=True,
        )
        self.linter.check_status()
        # check_status returns only when failing lint messages are being ignored.
        raise ValueError(details)

    def _parse_url_parts(self) -> tuple[str, list[tuple[str, str]]]:
        try:
            parsed = urlsplit(self.query_str)
            parameters = parse_qsl(
                parsed.query,
                keep_blank_values=True,
                strict_parsing=True,
            )
        except ValueError as exc:
            self._syntax_error(str(exc))

        if parsed.scheme not in {"http", "https"}:
            self._syntax_error("Crossref URLs must use HTTP or HTTPS.")
        if parsed.netloc.lower() != "api.crossref.org":
            self._syntax_error("URL host must be api.crossref.org.")
        if parsed.fragment:
            self._syntax_error("Crossref API URLs must not include a fragment.")
        endpoint = parsed.path.rstrip("/")
        if endpoint not in SUPPORTED_PATHS:
            self._syntax_error("Only the Crossref /works endpoint is supported.")
        return endpoint, parameters

    def _parse_parameters(
        self, parameters: list[tuple[str, str]]
    ) -> tuple[list[str | Query], list[tuple[str, str]]]:
        terms: list[str | Query] = []
        options = []
        for name, value in parameters:
            if name in QUERY_FIELDS:
                if not value.strip():
                    self._syntax_error(f"Crossref parameter {name!r} is empty.")
                terms.append(
                    Term(
                        value=value,
                        field=SearchField(QUERY_FIELDS[name]),
                        platform=PLATFORM.CROSSREF.value,
                    )
                )
            elif name.startswith("query."):
                self._syntax_error(f"Unsupported Crossref search parameter: {name}.")
            elif name in SUPPORTED_OPTIONS:
                options.append((name, value))
            else:
                self._syntax_error(f"Unsupported Crossref URL parameter: {name}.")
        return terms, options

    def parse(self) -> Query:
        """Parse a Crossref API URL into its supported search terms."""

        endpoint, parameters = self._parse_url_parts()
        terms, options = self._parse_parameters(parameters)
        if not terms:
            self._syntax_error("Crossref URL must include a supported query parameter.")

        query: Query
        if len(terms) == 1:
            term = terms[0]
            assert isinstance(term, Query)
            query = term
        else:
            query = AndQuery(terms, platform=PLATFORM.CROSSREF.value)

        setattr(query, "crossref_endpoint", endpoint)
        setattr(query, "crossref_options", options)
        self.linter.validate_query_tree(query)
        self.linter.check_status()
        return query


class CrossrefListParser(QueryListParser):
    """Reject list-style input, which is not a Crossref API URL format."""

    VERSION = "1"

    def __init__(
        self,
        query_list: str,
        *,
        field_general: str = "",
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_list=query_list,
            parser_class=CrossrefParser,
            field_general=field_general,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter: QueryListLinter = QueryListLinter(
            parser=self,
            string_parser_class=CrossrefParser,
            original_query_str=query_list,
            ignore_failing_linter=ignore_failing_linter,
        )

    def parse(self) -> Query:
        self.linter.add_message(
            QueryErrorCode.INVALID_SYNTAX,
            list_position=-1,
            positions=[(0, len(self.query_list))],
            details="Crossref API URLs do not support list-style queries.",
            fatal=True,
        )
        self.linter.check_status()
        raise ListQuerySyntaxError(self.linter)
