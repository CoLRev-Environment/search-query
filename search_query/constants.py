#!/usr/bin/env python
"""Constants for search-query"""
# pylint: disable=too-few-public-methods
# pylint: disable=line-too-long
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

# noqa: E501


class PLATFORM(Enum):
    """Database identifier"""

    WOS = "wos"
    PUBMED = "pubmed"
    EBSCO = "ebscohost"
    STRUCTURED = "structured"
    PRE_NOTATION = "pre_notation"


class TokenTypes(Enum):
    """Token types"""

    LOGIC_OPERATOR = "LOGIC_OPERATOR"
    PROXIMITY_OPERATOR = "PROXIMITY_OPERATOR"
    FIELD = "FIELD"
    SEARCH_TERM = "SEARCH_TERM"
    PARENTHESIS_OPEN = "PARENTHESIS_OPEN"
    PARENTHESIS_CLOSED = "PARENTHESIS_CLOSED"


@dataclass
class Token:
    """Token class"""

    value: str
    type: TokenTypes
    position: Tuple[int, int]


class Operators:
    """Operators"""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    NEAR = "NEAR"
    WITHIN = "WITHIN"


class Fields:
    """Search fields"""

    TITLE = "ti"
    ALL = "all"
    ABSTRACT = "ab"
    AUTHOR_KEYWORDS = "au"
    KEYWORDS = "kw"
    SUBJECT_TERMS = "st"
    SOURCE = "so"
    ISSN = "is"
    ISBN = "ib"
    LANGUAGE = "la"
    DESCRIPTORS = "de"

    @classmethod
    def all(cls) -> list:
        """Return all fields as a list."""
        return [
            value
            for key, value in vars(cls).items()
            if not key.startswith("_") and not callable(value) and key not in ["all"]
        ]


# The PLATFORM_FIELD_MAP contains the current mapping of standard Fields to the
# syntax of the databases. If a field is not present in the map, it is assumed
# that the field is not supported by the database.
# If multiple options exist for valid database syntax, only the most common
# option is included in the map. Less common options are replaced in the parser.
# For instance, pubmed recommends [mh]. However, [mesh] is also valid and is replaced
# in the parser.
PLATFORM_FIELD_MAP = {
    # fields from
    # https://webofscience.help.clarivate.com/en-us/Content/wos-core-collection/woscc-search-field-tags.htm
    PLATFORM.WOS: {
        Fields.ALL: "ALL=",
        Fields.ABSTRACT: "AB=",
        Fields.TITLE: "TI=",
    },
    # fields from https://pubmed.ncbi.nlm.nih.gov/help/
    PLATFORM.PUBMED: {
        Fields.ALL: "[all]",
        Fields.TITLE: "[ti]",
        Fields.ABSTRACT: "[ab]",
    },
    # fields from https://connect.ebsco.com/s/article/Searching-with-Field-Codes?language=en_US
    PLATFORM.EBSCO: {
        Fields.TITLE: "TI",
        Fields.ABSTRACT: "AB",
        Fields.ALL: "TX",
        Fields.AUTHOR_KEYWORDS: "AU",
        Fields.SUBJECT_TERMS: "SU",
        Fields.SOURCE: "SO",
        Fields.ISSN: "IS",
        Fields.ISBN: "IB",
        Fields.LANGUAGE: "LA",
        Fields.KEYWORDS: "KW",
        Fields.DESCRIPTORS: "DE",
    },
}

# For convenience, modules can use the following to translate fields to a DB
PLATFORM_FIELD_TRANSLATION_MAP = {
    db: {v: k for k, v in fields.items()} for db, fields in PLATFORM_FIELD_MAP.items()
}

PLATFORM_COMBINED_FIELDS_MAP = {
    PLATFORM.PUBMED: {
        "[tiab]": [Fields.TITLE, Fields.ABSTRACT],
    },
}


class ExitCodes:
    """Exit codes"""

    SUCCESS = 0
    FAIL = 1


class Colors:
    """Colors for CLI printing"""

    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


class QueryErrorCode(Enum):
    """Error codes for the query parser"""

    # Fatal errors (prefix: F)
    TOKENIZING_FAILED = (
        ["all"],
        "F0001",
        "tokenizing-failed",
        "Fatal error during tokenization",
        "",
    )
    UNBALANCED_PARENTHESES = (
        ["all"],
        "F0002",
        "unbalanced-parentheses",
        "Parentheses are unbalanced in the query",
        """**Typical fix**: Check the parentheses in the query

**Problematic query**:

.. code-block:: python

    (a AND b OR c

**Correct query**:

.. code-block:: python

    (a AND b) OR c""",
    )
    MISSING_OPERATOR = (
        ["all"],
        "F0003",
        "missing-operator",
        "An operator is missing between terms",
        "",
    )

    # Errors (prefix: E)
    SEARCH_FIELD_CONTRADICTION = (
        ["all"],
        "E0001",
        "search-field-contradiction",
        "Contradictory search fields specified",
        "",
    )
    SEARCH_FIELD_MISSING = (
        ["all"],
        "E0002",
        "search-field-missing",
        "Expected search field is missing",
        "",
    )
    SEARCH_FIELD_UNSUPPORTED = (
        ["all"],
        "E0003",
        "search-field-unsupported",
        "Search field is not supported for this database",
        "",
    )
    INVALID_TOKEN_SEQUENCE = (
        [PLATFORM.EBSCO],
        "E0004",
        "invalid-token-sequence",
        "The sequence of tokens is invalid "
        "([token_type] followed by [token_type] is not allowed)",
        "",
    )

    # Warnings (prefix: W)
    SEARCH_FIELD_REDUNDANT = (
        ["all"],
        "W0001",
        "search-field-redundant",
        "Recommend specifying search field only once in the search string",
        "",
    )
    SEARCH_FIELD_EXTRACTED = (
        ["all"],
        "W0002",
        "search-field-extracted",
        "Recommend explicitly specifying the search field in the string",
        "",
    )
    SEARCH_FIELD_NOT_SPECIFIED = (
        ["all"],
        "W0003",
        "search-field-not-specified",
        "Search field should be explicitly specified",
        "",
    )
    QUERY_STRUCTURE_COMPLEX = (
        ["all"],
        "W0004",
        "query-structure-unnecessarily-complex",
        "Query structure is more complex than necessary",
        "",
    )
    OPERATOR_CAPITALIZATION = (
        ["all"],
        "W0005",
        "operator-capitalization",
        "Operator should be in upper case",
        "",
    )

    # pylint: disable=too-many-arguments
    def __init__(
        self, scope: list, code: str, label: str, message: str, docs: str
    ) -> None:
        self.scope = scope
        self.code = code
        self.label = label
        self.message = message
        self.docs = docs

    # Error type is defined by first letter
    def is_fatal(self) -> bool:
        """Check if error is fatal"""
        return self.code.startswith("F")

    def is_error(self) -> bool:
        """Check if error is an error"""
        return self.code.startswith("E")

    def is_warning(self) -> bool:
        """Check if error is a warning"""
        return self.code.startswith("W")
