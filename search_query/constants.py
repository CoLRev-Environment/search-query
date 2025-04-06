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
    EBSCO = "ebsco"
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


class Fields:
    """Search fields"""

    TITLE = "ti"
    ALL = "all"
    ABSTRACT = "ab"
    AUTHOR_KEYWORDS = "au"

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
        Fields.TITLE: "TI ",
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

    # -------------------------------------------------------
    # Fatal errors (prefix: F)
    # -------------------------------------------------------
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
    UNMATCHED_OPENING_PARENTHESIS = (
        ["all"],
        "F0004",
        "unmatched-opening-parenthesis",
        "Unmatched opening parenthesis",
        """**Typical fix**: Check the parentheses in the query
**Problematic query**:
.. code-block:: python

    (a AND b OR c
**Correct query**:
.. code-block:: python


    (a AND b) OR c""",
    )
    UNMATCHED_CLOSING_PARENTHESIS = (
        ["all"],
        "F0005",
        "unmatched-closing-parenthesis",
        "Unmatched closing parenthesis",
        """**Typical fix**: Check the parentheses in the query
**Problematic query**:
.. code-block:: python
    a AND b) OR c
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
    INVALID_OPERATOR_POSITION = (
        [PLATFORM.PUBMED],
        "F0004",
        "invalid-operator-position",
        "Invalid operator position",
        "",
    )
    INVALID_SEARCH_FIELD_POSITION = (
        [PLATFORM.PUBMED],
        "F0005",
        "invalid-search-field-position",
        "Search field tags should directly follow search terms",
        "",
    )
    NESTED_NOT_QUERY = (
        [PLATFORM.PUBMED],
        "F0006",
        "nested-not-query",
        "Nesting of NOT operator is not supported for this database",
        "",
    )
    EMPTY_PARENTHESES = (
        [PLATFORM.PUBMED],
        "F0007",
        "empty-parentheses",
        "Query contains empty parentheses",
        "",
    )
    WILDCARD_IN_YEAR = (
        [PLATFORM.WOS],
        "F1001",
        "wildcard-in-year",
        "Wildcard characters (*, ?, $) not supported in year search.",
        """**Typical fix**: Replace with year range.

**Problematic query**:

.. code-block:: python

    A AND year=201*

**Correct query**:

.. code-block:: python

    A AND (year >= 2010 AND year < 2020)""",
    )
    UNSUPPORTED_WILDCARD = (
        [PLATFORM.WOS],
        "F1002",
        "unsupported-wildcard",
        "Unsupported wildcard in search string.",
        "",
    )
    WILDCARD_RIGHT_SHORT_LENGTH = (
        [PLATFORM.WOS],
        "F1003",
        "wildcard-short-length",
        "Right-hand wildcard must preceded by at least three characters.",
        "",
    )
    WILDCARD_AFTER_SPECIAL_CHAR = (
        [PLATFORM.WOS],
        "F1004",
        "wildcard-after-special-char",
        "Wildcard cannot be preceded by special characters.",
        "",
    )
    # TODO : consolidate with INVALID_TOKEN_SEQUENCE (EBSCO) is non-fatal?!
    INVALID_TOKEN_SEQUENCE_TWO_SEARCH_FIELDS = (
        [PLATFORM.EBSCO],
        "F1005",
        "invalid-token-sequence-two-search-fields",
        "Invalid token sequence: two search fields in a row.",
        "",
    )
    INVALID_TOKEN_SEQUENCE_TWO_OPERATORS = (
        [PLATFORM.EBSCO],
        "F1006",
        "invalid-token-sequence-two-operators",
        "Invalid token sequence: two operators in a row.",
        "",
    )
    NEAR_DISTANCE_TOO_LARGE = (
        [PLATFORM.WOS],
        "F1007",
        "near-distance-too-large",
        "NEAR distance is too large (max: 15).",
        "",
    )
    WILDCARD_STANDALONE = (
        [PLATFORM.WOS],
        "F1008",
        "wildcard-standalone",
        "Wildcard cannot be standalone.",
        "",
    )
    INVALID_TOKEN_SEQUENCE_MISSING_OPERATOR = (
        [PLATFORM.WOS],
        "F1009",
        "invalid-token-sequence-missing-operator",
        "Invalid token sequence: missing operator.",
        "",
    )
    WILDCARD_LEFT_SHORT_LENGTH = (
        [PLATFORM.WOS],
        "F1010",
        "wildcard-left-short-length",
        "Left-hand wildcard must be preceded by at least three characters.",
        "",
    )
    ISBN_FORMAT_INVALID = (
        [PLATFORM.WOS],
        "F1011",
        "isbn-format-invalid",
        "Invalid ISBN format.",
        "",
    )
    DOI_FORMAT_INVALID = (
        [PLATFORM.WOS],
        "F1012",
        "doi-format-invalid",
        "Invalid DOI format.",
        "",
    )

    # -------------------------------------------------------
    # Errors (prefix: E)
    # -------------------------------------------------------
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
    INVALID_CHARACTER = (
        [PLATFORM.PUBMED],
        "E0004",
        "invalid-character",
        "Search term contains invalid character",
        "",
    )
    INVALID_PROXIMITY_USE = (
        [PLATFORM.PUBMED],
        "E0005",
        "invalid-proximity-use",
        "Invalid use of the proximity operator :~",
        "",
    )
    INVALID_WILDCARD_USE = (
        [PLATFORM.PUBMED],
        "E0006",
        "invalid-wildcard-use",
        "Invalid use of the wildcard operator *",
        "",
    )
    QUERY_STARTS_WITH_PLATFORM_IDENTIFIER = (
        [PLATFORM.WOS],
        "E0005",
        "query-starts-with-platform-identifier",
        "Query starts with platform identifier",
        "",
    )
    QUERY_IN_QUOTES = (
        [PLATFORM.WOS],
        "E0006",
        "query-in-quotes",
        "The whole Search string is in quotes.",
        "",
    )

    # -------------------------------------------------------
    # Warnings (prefix: W)
    # -------------------------------------------------------
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
        "Operators should be capitalized",
        """**Typical fix**: Capitalize the operator
**Problematic query**:
.. code-block:: python
    a and b or c
**Correct query**:
.. code-block:: python
    a AND b OR c""",
    )
    IMPLICIT_NEAR_VALUE = (
        [PLATFORM.WOS],
        "W1000",
        "implicit-near-value",
        "The value of NEAR operator is implicit",
        """**Typical fix**: The parser automatically sets implicit NEAR values to the default of 15.

**Problematic query**:

.. code-block:: python

    A NEAR B

**Correct query**:

.. code-block:: python

    A NEAR/15 B""",
    )
    YEAR_SPAN_VIOLATION = (
        [PLATFORM.WOS],
        "W1001",
        "year-span-violation",
        "Year span must be five or less.",
        """**Typical fix**: The parser automatically sets the year span to 5.

**Problematic query**:

.. code-block:: python

    A AND PY=2000-2020

**Correct query**:

.. code-block:: python

    A AND PY=2015-2020""",
    )
    UNSUPPORTED_SEARCH_FIELD = (
        [PLATFORM.WOS],
        "W1002",
        "unsupported-search-field",
        "TODO",
        "",
    )
    OPERATOR_CHANGED_AT_SAME_LEVEL = (
        ["all"],
        "W1003",
        "operator-changed-at-same-level",
        "Operator changed at the same level (currently relying on implicit operator precedence, explicit parentheses are recommended)",
        "",
    )
    QUERY_PRECEDENCE = (
        [PLATFORM.PUBMED],
        "W0005",
        "query-precedence-warning",
        "AND operator used after OR operator in the same subquery",
        "",
    )

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
