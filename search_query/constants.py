#!/usr/bin/env python
"""Constants for search-query"""
import typing
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

# noqa: E501

# pylint: disable=too-few-public-methods
# pylint: disable=line-too-long


class PLATFORM(Enum):
    """Database identifier"""

    WOS = "wos"
    PUBMED = "pubmed"
    EBSCO = "ebscohost"
    GENERIC = "generic"
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
    RANGE_OPERATOR = "RANGE_OPERATOR"
    UNKNOWN = "UNKNOWN"


class OperatorNodeTokenTypes(Enum):
    """Operator node token types (list queries)"""

    LIST_ITEM_REFERENCE = "LIST_ITEM_REFERENCE"
    LOGIC_OPERATOR = "LOGIC_OPERATOR"
    UNKNOWN = "UNKNOWN"


class ListTokenTypes(Enum):
    """List token types"""

    OPERATOR_NODE = "OPERATOR_NODE"
    QUERY_NODE = "QUERY_NODE"


GENERAL_ERROR_POSITION = -1


@dataclass
class Token:
    """Token class"""

    value: str
    type: TokenTypes
    position: Tuple[int, int]

    def is_operator(self) -> bool:
        """Check if token is an operator"""
        return self.type in (TokenTypes.LOGIC_OPERATOR, TokenTypes.PROXIMITY_OPERATOR)


@dataclass
class ListToken:
    """Token class"""

    value: str
    type: OperatorNodeTokenTypes
    level: int
    position: Tuple[int, int]


# pylint: disable=too-few-public-methods
class SearchField:
    """SearchField class."""

    def __init__(
        self,
        value: str,
        *,
        position: typing.Optional[typing.Tuple[int, int]] = None,
    ) -> None:
        """init method"""
        self.value = value
        self.position = position

    def __str__(self) -> str:
        return self.value

    def copy(self) -> "SearchField":
        """Return a copy of the SearchField instance."""
        return SearchField(self.value, position=self.position)


class Operators:
    """Operators"""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    NEAR = "NEAR"
    WITHIN = "WITHIN"
    RANGE = "RANGE"


class Fields:
    """Search fields"""

    TITLE = "title"
    ALL = "all-fields"
    ABSTRACT = "abstract"
    TOPIC = "topic"
    LANGUAGE = "language"
    YEAR_PUBLICATION = "year-publication"
    TEXT_WORD = "text-word"

    RESEARCH_AREA = "research-area"
    WEB_OF_SCIENCE_CATEGORY = "wos-category"
    MESH_TERM = "mesh-term"
    FILTER = "sb"
    SUBJECT_TERMS = "subject-terms"
    SOURCE = "source"
    DESCRIPTORS = "descriptors"

    AUTHOR_KEYWORDS = "keywords-author"
    KEYWORDS = "keywords"
    KEYWORDS_PLUS = "keywords-plus"
    GROUP_AUTHOR = "group-author"

    JOURNAL = "journal"
    PUBLICATION_TYPE = "publication-type"
    CONFERENCE = "conference"
    PUBLISHER = "publisher"
    PUBLICATION_NAME = "publication-name"

    AUTHOR = "author"
    AUTHOR_IDENTIFIERS = "author-identifiers"
    EDITOR = "editor"
    AFFILIATION = "affiliation"

    DOI = "doi"
    PUBMED_ID = "pmid"
    ACCESSION_NUMBER = "accession-nr"

    GRANT_NUMBER = "grant-nr"
    FUNDING_AGENCY = "funding-agency"
    FUNDING_TEXT = "funding-text"

    ISSN = "issn"
    ISBN = "isbn"
    ISSN_ISBN = "issn-isbn"

    ORGANIZATION_ENHANCED = "organization-enhanced"
    ORGANIZATION = "organization"
    CITY = "city"
    ADDRESS = "address"
    ZIP_POSTAL_CODE = "zip"
    COUNTRY_REGION = "country-region"
    PROVINCE_STATE = "province-state"
    STREET_ADDRESS = "street-address"
    SUBORGANIZATION = "suborganization"

    @classmethod
    def all(cls) -> list:
        """Return all fields as a list."""
        return [
            value
            for key, value in vars(cls).items()
            if not key.startswith("_") and not callable(value) and key not in ["all"]
        ]


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
    GREY = "\033[90m"
    END = "\033[0m"


class LinterMode:
    """Linter mode"""

    STRICT = "strict"
    NONSTRICT = "non-strict"


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
        "F1001",
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
    UNBALANCED_QUOTES = (
        ["all"],
        "F1002",
        "unbalanced-quotes",
        "Quotes are unbalanced in the query",
        "",
    )

    # merged with INVALID_OPERATOR_POSITION, INVALID_SEARCH_FIELD_POSITION
    INVALID_TOKEN_SEQUENCE = (
        [PLATFORM.EBSCO],
        "F1004",
        "invalid-token-sequence",
        # Note: provide details like
        # ([token_type] followed by [token_type] is not allowed)
        "The sequence of tokens is invalid." "",
        "",
    )
    EMPTY_PARENTHESES = (
        [PLATFORM.PUBMED],
        "F1009",
        "empty-parentheses",
        "Query contains empty parentheses",
        "",
    )
    INVALID_SYNTAX = (
        ["all"],
        "F1010",
        "invalid-syntax",
        "Query contains invalid syntax",
        "",
    )
    TOO_MANY_OPERATORS = (
        [PLATFORM.WOS],
        "F1011",
        "too-many-operators",
        "Too many operators in the query",
        "",
    )
    TOO_MANY_SEARCH_TERMS = (
        [PLATFORM.WOS],
        "F1012",
        "too-many-search-terms",
        "Too many search terms in the query",
        "",
    )

    WILDCARD_UNSUPPORTED = (
        [PLATFORM.WOS],
        "F2001",
        "wildcard-unsupported",
        "Unsupported wildcard in search string.",
        "",
    )
    WILDCARD_IN_YEAR = (
        [PLATFORM.WOS],
        "F2002",
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
    WILDCARD_RIGHT_SHORT_LENGTH = (
        [PLATFORM.WOS],
        "F2003",
        "wildcard-right-short-length",
        "Right-hand wildcard must preceded by at least three characters.",
        """**Typical fix**: Replace short wildcard prefix with at least three characters or use a more specific term.

**Problematic query**:

.. code-block:: python

    TI=te*
    TS=ca*

**Correct query**:

.. code-block:: python

    TI=tech*
    TS=cat*""",
    )
    WILDCARD_LEFT_SHORT_LENGTH = (
        [PLATFORM.WOS],
        "F2004",
        "wildcard-left-short-length",
        "Left-hand wildcard must be preceded by at least three characters.",
        """**Typical fix**: Ensure the term before a left-hand wildcard (*) has at least three characters.
        
**Problematic query**:

.. code-block:: python

    TI=*te

**Correct query**:

.. code-block:: python

    TI=abc*te""",
    )
    WILDCARD_AFTER_SPECIAL_CHAR = (
        [PLATFORM.WOS],
        "F2005",
        "wildcard-after-special-char",
        "Wildcard cannot be preceded by special characters.",
        """**Typical fix**: Remove the special character before the wildcard or rephrase the query to avoid combining them.
        
**Problematic query**:

.. code-block:: python

    TI=(term1 term2!*)

**Correct query**:

.. code-block:: python

    TI=(term1 term2*)""",
    )
    WILDCARD_STANDALONE = (
        [PLATFORM.WOS],
        "F2006",
        "wildcard-standalone",
        "Wildcard cannot be standalone.",
         """**Typical fix**: Replace the standalone wildcard with a complete search term or remove it entirely.
        
**Problematic query**:

.. code-block:: python

    TI=term1 AND "?"

**Correct query**:

.. code-block:: python

    TI=term1""",
    )
    NEAR_DISTANCE_TOO_LARGE = (
        [PLATFORM.WOS],
        "F2007",
        "near-distance-too-large",
        "NEAR distance is too large (max: 15).",
        """**Typical fix**: Reduce the NEAR distance to 15 or less.
        
**Problematic query**:

.. code-block:: python

    TI=term1 NEAR/20 term2

**Correct query**:

.. code-block:: python

    TI=term1 NEAR/15 term2""",
    )
    ISBN_FORMAT_INVALID = (
        [PLATFORM.WOS],
        "F2008",
        "isbn-format-invalid",
        "Invalid ISBN format.",
        """**Typical fix**: Use a valid ISBN-10 or ISBN-13 format (e.g., 10 or 13 digits, optionally with hyphens in correct positions).
        
**Problematic query**:

.. code-block:: python

    IS=978-3-16-148410-0

**Correct query**:

.. code-block:: python

    IS=978-3-16-148410-0""",
    )
    DOI_FORMAT_INVALID = (
        [PLATFORM.WOS],
        "F2009",
        "doi-format-invalid",
        "Invalid DOI format.",
        """**Typical fix**: Use a valid DOI format (e.g., starts with 10. followed by a numeric string and suffix).
        
**Problematic query**:

.. code-block:: python

    DO=12.1000/xyz

**Correct query**:

.. code-block:: python

    DO=10.1000/xyz""",
    )
    YEAR_SPAN_VIOLATION = (
        [PLATFORM.WOS],
        "F2010",
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
    SEARCH_FIELD_UNSUPPORTED = (
        ["all", PLATFORM.WOS],
        "F2011",
        "search-field-unsupported",
        "Search field is not supported for this database",
        """**Typical fix**: Replace the unsupported field with a supported one for the selected database.

**Problematic query**:

.. code-block:: python

    TI=term1 AND IY=digital

**Correct query**:

.. code-block:: python

    TI=term1 AND PY=digital""",
    )
    YEAR_WITHOUT_SEARCH_TERMS = (
        [PLATFORM.WOS],
        "F2012",
        "year-without-search-terms",
        "A search for publication years must include at least another search term.",
        """**Typical fix**: Combine the year filter with at least one other search term.

**Problematic query**:

.. code-block:: python

    PY=200*

**Correct query**:

.. code-block:: python

    TI=term AND PY=200*""",
    )
    NESTED_QUERY_WITH_SEARCH_FIELD = (
        [PLATFORM.PUBMED],
        "F2013",
        "nested-query-with-search-field",
        "A Nested query cannot have a search field.",
        """**Typical fix**: Remove the search field from the nested query (operator) since nested queries cannot have search fields.
**Problematic query**:

.. code-block:: python

    OrQuery(
    [
        Term("health tracking"),
        Term("remote monitoring"),
    ],
    search_field="[tiab]",
    platform=PLATFORM.PUBMED.value,
)

**Correct query**:

.. code-block:: python

    OrQuery(
    [
        Term("health tracking"),
        Term("remote monitoring"),
    ],
    platform=PLATFORM.PUBMED.value,
)""",
    )
    YEAR_FORMAT_INVALID = (
        [PLATFORM.WOS],
        "F2014",
        "year-format-invalid",
        "Invalid year format.",
        """**Typical fix**: Use a valid numeric year format (e.g., 4-digit year).

**Problematic query**:

.. code-block:: python

    TI=term1 AND PY=20xy

**Correct query**:

.. code-block:: python

    TI=term1 AND PY=2020""",
    )

    MISSING_ROOT_NODE = (
        [PLATFORM.WOS],
        "F3001",
        "missing-root-node",
        "List format query without root node (typically containing operators)",
        # The last item of the list must be a "combining string"
        """**Typical fix**: Add a root-level operator to combine the list items into a single query.

**Problematic query**:

.. code-block:: python

    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat" OR "acrobats")

**Correct query**:

.. code-block:: python

    TS=("Peer leader*" OR "Shared leader*") OR TS=("acrobatics" OR "acrobat" OR "acrobats")""",
    )
    MISSING_OPERATOR_NODES = (
        [PLATFORM.WOS],
        "F3002",
        "missing-operator-nodes",
        "List format query without operator nodes",
        "",
    )
    INVALID_LIST_REFERENCE = (
        [PLATFORM.WOS, PLATFORM.PUBMED],
        "F3003",
        "invalid-list-reference",
        "Invalid list reference in list query",
        """**Typical fix**: Reference only existing list items in your query.

**Problematic query**:

.. code-block:: python 
# PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat" OR "acrobats")
    3. #1 AND #5
# PLATFORM.PUBMED:
    1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] AND Distributed leader*[Title/Abstract])
    2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
    3. #1 AND #2 AND #4
**Correct query**:

.. code-block:: python
# PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat" OR "acrobats")
    3. #1 AND #2
# PLATFORM.PUBMED:
    1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] AND Distributed leader*[Title/Abstract])
    2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
    3. #1 AND #2
    """,
    )

    # -------------------------------------------------------
    # Errors (prefix: E)
    # -------------------------------------------------------
    # Note: merged SEARCH_FIELD_NOT_SPECIFIED:
    SEARCH_FIELD_MISSING = (
        ["all"],
        "E0001",
        "search-field-missing",
        "Expected search field is missing", 
        "",
    )
    SEARCH_FIELD_CONTRADICTION = (
        ["all"],
        "E0002",
        "search-field-contradiction",
        "Contradictory search fields specified",
        """**Typical fix**: Ensure that the search fields used in the query and the general search field parameter are consistent.

**Problematic query**:

.. code-block:: python 
# PLATFORM.WOS:
    TI=(digital AND online)
# PLATFORM.PUBMED:
    "eHealth"[tiab] "digital health"[tiab]
    search_field_general = Title

**Correct query**:

.. code-block:: python
# PLATFORM.WOS:
    digital AND online
# PLATFORM.PUBMED:
    "eHealth"[Title] "digital health"[Title]
    search_field_general = Title""",
    )

    INVALID_CHARACTER = (
        [PLATFORM.PUBMED],
        "E0004",
        "invalid-character",
        "Search term contains invalid character",
        "",
    )
    INVALID_PROXIMITY_USE = (
        [PLATFORM.PUBMED, PLATFORM.EBSCO],
        "E0005",
        "invalid-proximity-use",
        "Invalid use of the proximity operator",
        "",
    )
    INVALID_WILDCARD_USE = (
        [PLATFORM.PUBMED],
        "E0006",
        "invalid-wildcard-use",
        "Invalid use of the wildcard operator *",
        """**Typical fix**: Avoid using wildcards (*) with short strings (less than 4 characters). Specify search fields directly in the query instead of relying on general search field settings.

**Problematic query**:

.. code-block:: python 

    "health tracking" AND AI*

**Correct query**:

.. code-block:: python

    "health tracking" AND AID*""",
    )
    QUERY_STARTS_WITH_PLATFORM_IDENTIFIER = (
        [PLATFORM.WOS],
        "E0007",
        "query-starts-with-platform-identifier",
        "Query starts with platform identifier",
        "",
    )
    QUERY_IN_QUOTES = (
        [PLATFORM.WOS],
        "E0008",
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
        """**Typical fix**: Specify the search field either globally or within the search terms, but not both. (PUBMED)

**Problematic query**:

.. code-block:: python 

    eHealth[ti]

**Correct query**:

.. code-block:: python

    eHealth""",
    )
    SEARCH_FIELD_EXTRACTED = (
        ["all"],
        "W0002",
        "search-field-extracted",
        "Recommend explicitly specifying the search field in the string",
        """**Typical fix**: Explicitly specify the search fields in the query string rather than relying on a general search field setting. (EBSCO)

**Problematic query**:

.. code-block:: python 

    TI Artificial Intelligence AND AB Future

**Correct query**:

.. code-block:: python

    TI Artificial Intelligence AND AB Future""",
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
        "W0006",
        "implicit-near-value",
        "The value of NEAR operator is implicit",
        """**Typical fix**: The parser automatically sets NEAR values to 15 (default).

**Problematic query**:

.. code-block:: python

    A NEAR B

**Correct query**:

.. code-block:: python

    A NEAR/15 B""",
    )
    # Note : merged QUERY_PRECEDENCE and OPERATOR_CHANGED_AT_SAME_LEVEL into:
    IMPLICIT_PRECEDENCE = (
        ["all", PLATFORM.PUBMED],
        "W0007",
        "implicit-precedence",
        "Operator changed at the same level (explicit parentheses are recommended)",
        """**Typical fix**: Use explicit parentheses to clarify operator precedence and avoid ambiguity in mixed AND/OR queries.

**Problematic query**:

.. code-block:: python
# PLATFORM.PUBMED
   "health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")
# PLATFORM.WOS
    TI=term1 AND OR
**Correct query**:

.. code-block:: python
# PLATFORM.PUBMED
    ("health tracking" OR ("remote" AND "monitoring")) AND ("mobile application" OR "wearable device")
# PLATFORM.WOS
    TI=term1 AND ( ... ) OR ( ... )
    """,
    )
    TOKEN_AMBIGUITY = (["all"], "W0008", "token-ambiguity", "Token ambiguity", "")
    BOOLEAN_OPERATOR_READABILITY = (
        ["all"],
        "W0009",
        "boolean-operator-readability",
        "Boolean operator readability",
        "",
    )
    CHARACTER_REPLACEMENT = (
        [PLATFORM.PUBMED],
        "W0010",
        "character-replacement",
        "Character replacement",
        """**Typical fix**: Be aware that certain characters like . in search terms will be replaced with whitespace due to platform-specific conversions. Specify search fields explicitly within the query instead of relying on general settings.

**Problematic query**:

.. code-block:: python

    "healthcare" AND "Industry 4.0"

**Correct query**:

.. code-block:: python

    "healthcare" AND "Industry 4 0" """,
    )
    DATE_FILTER_IN_SUBQUERY = (
        [PLATFORM.PUBMED],
        "W0011",
        "date-filter-in-subquery",
        "Date filter in subquery",
        """**Typical fix**: Apply date filters at the top-level of the query instead of inside subqueries to ensure the date restriction applies as intended.

**Problematic query**:

.. code-block:: python

    (("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) AND 2019/01/01:2019/12/01[publication date]) OR ("ehealth"[Title/Abstract])
    device[ti] OR (wearable[ti] AND 2000:2010[dp])

**Correct query**:

.. code-block:: python

    (("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) OR ("ehealth"[Title/Abstract])) AND 2019/01/01:2019/12/01[publication date]
    (device[ti] OR wearable[ti]) AND 2000:2010[dp]""",
    )
    IMPLICIT_OPERATOR = (
        [PLATFORM.PUBMED],
        "W0012",
        "implicit-operator",
        "Implicit operator",
        "",
    )
    NON_STANDARD_QUOTES = (
        ["all"],
        "W0013",
        "non-standard-quotes",
        "Non-standard quotes",
        """**Typical fix**: Replace non-standard quotes (e.g., “ ”) with standard ASCII quotes (").

**Problematic query**:

.. code-block:: python

    TS=“carbon”

**Correct query**:

.. code-block:: python

    TS="carbon" """,
    )
    JOURNAL_FILTER_IN_SUBQUERY = (
        [PLATFORM.PUBMED],
        "W0014",
        "journal-filter-in-subquery",
        "Journal (or publication name) filter in subquery",
        """**Typical fix**: Apply journal (publication name) filters at the top level of the query instead of inside subqueries to ensure the filter applies to the entire result set.

**Problematic query**:

.. code-block:: python

    "activity"[Title/Abstract] AND ("cancer"[Title/Abstract] AND "Lancet"[Journal])

**Correct query**:

.. code-block:: python

    ("activity"[Title/Abstract] AND "cancer"[Title/Abstract]) AND "Lancet"[Journal] """,
    )
    UNSUPPORTED_PREFIX = (
        [PLATFORM.PUBMED],
        "W0015",
        "unsupported-prefix",
        "Unsupported prefix in search query",
        """**Typical fix**: Remove unsupported prefixes or introductory text from the search query to ensure it runs correctly.

**Problematic query**:

.. code-block:: python

   Pubmed with no restrictions: (eHealth[Text Word])

**Correct query**:

.. code-block:: python

    eHealth[Text Word] """,
    )
    UNSUPPORTED_SUFFIX = (
        [PLATFORM.PUBMED],
        "W0016",
        "unsupported-suffix",
        "Unsupported suffix in search query",
        """**Typical fix**: Remove unsupported suffixes or trailing text from the search query to avoid errors.

**Problematic query**:

.. code-block:: python

   (eHealth[Text Word]) Sort by: Publication Date

**Correct query**:

.. code-block:: python

    (eHealth[Text Word]) """,
    )

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
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

    # Note: needed for the documentation:
    def is_error(self) -> bool:  # pragma: no cover
        """Check if error is an error"""
        return self.code.startswith("E")

    # Note: needed for the documentation:
    def is_warning(self) -> bool:  # pragma: no cover
        """Check if error is a warning"""
        return self.code.startswith("W")
