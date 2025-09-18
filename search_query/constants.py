#!/usr/bin/env python
"""Constants for search-query"""
from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

# flake8: noqa: E501
# ruff: noqa: E501

# pylint: disable=too-few-public-methods
# pylint: disable=line-too-long
# pylint: disable=too-many-lines


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
    TERM = "TERM"
    PARENTHESIS_OPEN = "PARENTHESIS_OPEN"
    PARENTHESIS_CLOSED = "PARENTHESIS_CLOSED"
    RANGE_OPERATOR = "RANGE_OPERATOR"
    UNKNOWN = "UNKNOWN"


class OperatorNodeTokenTypes(Enum):
    """Operator node token types (list queries)"""

    LIST_ITEM_REFERENCE = "LIST_ITEM_REFERENCE"
    NON_LIST_ITEM_REFERENCE = "NON_LIST_ITEM_REFERENCE"


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

    def copy(self) -> SearchField:
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


class QueryErrorCode(Enum):
    """Error codes for the query parser"""

    # -------------------------------------------------------
    # EBSCO
    # -------------------------------------------------------

    EBSCO_WILDCARD_UNSUPPORTED = (
        "EBSCO_0001",
        "wildcard-unsupported",
        "Unsupported wildcard in search string.",
        """
**Problematic query**:

.. code-block:: text

   # Leading wildcard
   TI=*Health

**Recommended query**:

.. code-block:: text

    TI=Health*

**Typical fix**:  Remove unsupported wildcard characters from the query.""",
    )

    EBSCO_INVALID_CHARACTER = (
        "EBSCO_0002",
        "invalid-character",
        "Search term contains invalid character",
        "",
    )

    # -------------------------------------------------------
    # Field
    # -------------------------------------------------------

    # Fields can be:
    # Extracted (recommendation not to use the field_general to avoid accidental errors)
    # Implicit or missing (depending on whether the platform adds a default field when it is not specified explicitly)

    # Note: merged field_NOT_SPECIFIED:
    FIELD_UNSUPPORTED = (
        "FIELD_0001",
        "field-unsupported",
        "Search field is not supported for this database",
        """
**Problematic query**:

.. code-block:: text

    TI=term1 AND IY=2020

**Recommended query**:

.. code-block:: text

    TI=term1 AND PY=2020

**Typical fix**: Replace the unsupported field with a supported one for the selected database.
""",
    )
    FIELD_MISSING = (
        "FIELD_0002",
        "field-missing",
        "Search field is missing",
        """
**Problematic query**:

.. code-block:: text

    # PLATFORM.PUBMED:
    "eHealth" OR "digital health"

**Recommended query**:

.. code-block:: text

    # PLATFORM.PUBMED:
    "eHealth"[all] OR "digital health"[all]
""",
    )
    FIELD_EXTRACTED = (
        "FIELD_0003",
        "field-extracted",
        "Recommend explicitly specifying the search field in the string",
        """
**Problematic query**:

.. code-block:: text

    # EBSCO search with general search field = "Title"
    Artificial Intelligence AND Future

**Recommended query**:

.. code-block:: text

    # EBSCO search without general search field
    TI Artificial Intelligence AND TI Future

**Typical fix**: Explicitly specify the search fields in the query string rather than relying on a general search field setting. (EBSCO)

**Rationale**: The search_string may be copied and the general_field missed, leading to incorrect reproduction of the query.
""",
    )
    FIELD_IMPLICIT = (
        "FIELD_0004",
        "field-implicit",
        "Search field is implicitly specified",
        """
**Problematic query**:

.. code-block:: text

    # PLATFORM.PUBMED:

    "eHealth" OR "digital health"

**Recommended query**:

.. code-block:: text

    # PLATFORM.PUBMED:

    "eHealth"[all] OR "digital health"[all]

**Typical fix**: Explicitly specify the search field in the query string instead of relying on a general search field setting.
""",
    )

    # -------------------------------------------------------
    # Linter
    # -------------------------------------------------------
    LINT_DEPRECATED_SYNTAX = (
        "LINT_2001",
        "deprecated-syntax",
        "deprecated-syntax",
        """This message indicates that the query uses deprecated syntax.

**Typical fix**: Update the query to use the latest syntax by running

```bash
search-query upgrade search_query.json --to 2.0.0
```""",
    )

    # -------------------------------------------------------
    # Parse
    # -------------------------------------------------------

    TOKENIZING_FAILED = (
        "PARSE_0001",
        "tokenizing-failed",
        "Fatal error during tokenization",
        """**Typical fix**: Check the query syntax and ensure it is correctly formatted.""",
    )
    UNBALANCED_PARENTHESES = (
        "PARSE_0002",
        "unbalanced-parentheses",
        "Parentheses are unbalanced in the query",
        """
**Problematic query**:

.. code-block:: text

    (a AND b OR c

**Recommended query**:

.. code-block:: text

    (a AND b) OR c

**Typical fix**: Check the parentheses in the query
""",
    )
    UNBALANCED_QUOTES = (
        "PARSE_0003",
        "unbalanced-quotes",
        "Quotes are unbalanced in the query",
        """
**Problematic query**:

.. code-block:: text

    "eHealth[ti]

**Recommended query**:

.. code-block:: text

    "eHealth"[ti]

**Typical fix**: Add the missing closing quote to balance the quotation marks.""",
    )

    # merged with INVALID_OPERATOR_POSITION, INVALID_field_POSITION
    INVALID_TOKEN_SEQUENCE = (
        "PARSE_0004",
        "invalid-token-sequence",
        # Note: provide details like
        # ([token_type] followed by [token_type] is not allowed)
        "The sequence of tokens is invalid." "",
        """**Problematic query**:

.. code-block:: texts

    # Example: Two operators in a row
    eHealth AND OR digital health

**Recommended query**:

.. code-block:: text

    eHealth OR digital health

**Typical fix**: Check the sequence of operators and terms in the query
""",
    )
    INVALID_SYNTAX = (
        "PARSE_0006",
        "invalid-syntax",
        "Query contains invalid syntax",
        """**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS
    eHealth[ti]

    # PLATFORM.PUBMED
    TI=eHealth

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS
    TI=eHealth

    # PLATFORM.PUBMED
    eHealth[ti]
""",
    )

    QUERY_IN_QUOTES = (
        "PARSE_0007",
        "query-in-quotes",
        "The whole Search string is in quotes.",
        """
**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS
    "eHealth[ti] AND digital health[ti]"

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS
    eHealth[ti] AND digital health[ti]
""",
    )
    UNSUPPORTED_PREFIX = (
        "PARSE_0008",
        "unsupported-prefix",
        "Unsupported prefix in search query",
        """
**Problematic query**:

.. code-block:: text

   Pubmed with no restrictions: (eHealth[ti])

**Recommended query**:

.. code-block:: text

    eHealth[ti]

**Typical fix**: Remove unsupported prefixes or introductory text from the search query to ensure it runs correctly.
""",
    )
    UNSUPPORTED_SUFFIX = (
        "PARSE_0009",
        "unsupported-suffix",
        "Unsupported suffix in search query",
        """
**Problematic query**:

.. code-block:: text

   (eHealth[ti]) Sort by: Publication Date

**Recommended query**:

.. code-block:: text

    (eHealth[ti])

**Typical fix**: Remove unsupported suffixes or trailing text from the search query to avoid errors.
""",
    )

    UNSUPPORTED_PREFIX_PLATFORM_IDENTIFIER = (
        "PARSE_0010",
        "unsupported-prefix-platform-identifier",
        "Query starts with platform identifier",
        """
**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS
    WOS: eHealth[ti]

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS
    eHealth[ti]
""",
    )

    LIST_QUERY_MISSING_ROOT_NODE = (
        "PARSE_1001",
        "list-query-missing-root-node",
        "List format query without root node (typically containing operators)",
        """
**Problematic query**:

.. code-block:: text

    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat" OR "acrobats")

**Recommended query**:

.. code-block:: text

    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat" OR "acrobats")
    3. #1 AND #2

**Typical fix**: Add a root-level operator to combine the list items into a single query.
""",
    )
    LIST_QUERY_INVALID_REFERENCE = (
        "PARSE_1002",
        "list-query-invalid-reference",
        "Invalid list reference in list query",
        """
**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat")
    3. #1 AND #5

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat")
    3. #1 AND #2

**Typical fix**: Reference only existing list items.
""",
    )

    # -------------------------------------------------------
    # PubMed
    # -------------------------------------------------------

    # Note: PubMed does not have INVALID_CHARACTER, but CHARACTER_REPLACEMENT

    NESTED_QUERY_WITH_FIELD = (
        "PUBMED_0001",
        "nested-query-with-field",
        "A Nested query cannot have a search field.",
        """
**Problematic query**:

.. code-block:: text

    eHealth[ti] AND ("health tracking" OR "remote monitoring")[tiab]

**Recommended query**:

.. code-block:: text

    eHealth[ti] AND ("health tracking"[tiab] OR "remote monitoring"[tiab])

**Typical fix**: Remove the search field from the nested query (operator) since nested queries cannot have search fields.
""",
    )

    CHARACTER_REPLACEMENT = (
        "PUBMED_0002",
        "character-replacement",
        "Character replacement",
        """
**Problematic query**:

.. code-block:: text

    "healthcare" AND "Industry 4.0"

**Recommended query**:

.. code-block:: text

    "healthcare" AND "Industry 4 0"

**Typical fix**: Be aware that certain characters like . in search terms will be replaced with whitespace due to platform-specific conversions. Specify search fields explicitly within the query instead of relying on general settings.
""",
    )

    INVALID_WILDCARD_USE = (
        "PUBMED_0003",
        "invalid-wildcard-use",
        "Invalid use of the wildcard operator *",
        """
**Problematic query**:

.. code-block:: text

    "health tracking" AND AI*

**Recommended query**:

.. code-block:: text

    "health tracking" AND AID*

**Typical fix**: Avoid using wildcards (*) with short strings (less than 4 characters). Specify search fields directly in the query instead of relying on general search field settings.
""",
    )

    # -------------------------------------------------------
    # Quality
    # -------------------------------------------------------

    QUERY_STRUCTURE_COMPLEX = (
        "QUALITY_0001",
        "query-structure-unnecessarily-complex",
        "Query structure is more complex than necessary",
        """
**Problematic query**:

.. code-block:: text

    # PLATFORM.EBSCO
    TI "sleep" OR TI "sleep disorders"

    # PLATFORM.EBSCO
    TI "sleep" AND TI "sleep disorders"


**Recommended query**:

.. code-block:: text

    # PLATFORM.EBSCO
    TI "sleep"

    # PLATFORM.EBSCO
    TI "sleep disorders"


**Typical fix**: Remove redundant terms when one term is already covered by a broader (OR) or encompassing (AND) term in the query.""",
    )

    DATE_FILTER_IN_SUBQUERY = (
        "QUALITY_0002",
        "date-filter-in-subquery",
        "Date filter in subquery",
        """
**Problematic query**:

.. code-block:: text

    (("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) AND 2019/01/01:2019/12/01[publication date]) OR ("ehealth"[Title/Abstract])
    device[ti] OR (wearable[ti] AND 2000:2010[dp])

**Recommended query**:

.. code-block:: text

    (("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) OR ("ehealth"[Title/Abstract])) AND 2019/01/01:2019/12/01[publication date]
    (device[ti] OR wearable[ti]) AND 2000:2010[dp]

**Typical fix**: Apply date filters at the top-level of the query instead of inside subqueries to ensure the date restriction applies as intended.
""",
    )

    JOURNAL_FILTER_IN_SUBQUERY = (
        "QUALITY_0003",
        "journal-filter-in-subquery",
        "Journal (or publication name) filter in subquery",
        """
**Problematic query**:

.. code-block:: text

    "activity"[Title/Abstract] OR ("cancer"[Title/Abstract] AND "Lancet"[Journal])

**Recommended query**:

.. code-block:: text

    ("activity"[Title/Abstract] OR "cancer"[Title/Abstract]) AND "Lancet"[Journal]

**Typical fix**: Apply journal (publication name) filters at the top level of the query instead of inside subqueries to ensure the filter applies to the entire result set.
""",
    )

    UNNECESSARY_PARENTHESES = (
        "QUALITY_0004",
        "unnecessary-parentheses",
        "Unnecessary parentheses in queries",
        """

**Problematic query**:

.. code-block:: text

    ("digital health" OR "eHealth") OR ("remote monitoring" OR "telehealth")

**Recommended query**:

.. code-block:: text

    "digital health" OR "eHealth" OR "remote monitoring" OR "telehealth

**Explanation**: Parentheses are unnecessary when all operators used are **associative and have equal precedence** (like a series of ORs or a series of ANDs). In such cases, the grouping does not influence the evaluation result and adds unnecessary complexity.""",
    )

    REDUNDANT_TERM = (
        "QUALITY_0005",
        "redundant-term",
        "Redundant term in the query",
        """
**Problematic query (AND)**:

.. code-block:: text

    "digital health" AND "health"

**Recommended query (AND)**:

.. code-block:: text

    "digital health"

.. note::

    The term "digital health" is more specific than "health".
    The AND query will not retrieve results that match "health" but not "digital health".
    Therefore, the more specific term ("digital health") is sufficient.

**Problematic query (OR)**:

.. code-block:: text

    "digital health" OR "health"

**Recommended query (OR)**:

.. code-block:: text

    "health"

.. note::

    The term "health" is broader than "digital health".
    In the OR query, all results that match "digital health" will also match "health".
    Therefore, the broader term ("health") is sufficient.

**Typical fix**: Remove redundant terms that do not add value to the query.""",
    )

    POTENTIAL_WILDCARD_USE = (
        "QUALITY_0006",
        "potential-wildcard-use",
        "Potential wildcard use",
        """
**Problematic query**:

.. code-block:: text

    computation OR computational OR computer OR computer science

**Recommended query**:

.. code-block:: text

    comput*""",
    )

    # -------------------------------------------------------
    # Structural
    # -------------------------------------------------------

    # Note : merged QUERY_PRECEDENCE and OPERATOR_CHANGED_AT_SAME_LEVEL into:
    IMPLICIT_PRECEDENCE = (
        "STRUCT_0001",
        "implicit-precedence",
        "Operator changed at the same level (explicit parentheses are recommended)",
        """
**Problematic query**:

.. code-block:: text

    # PLATFORM.PUBMED
   "health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")

**Recommended query**:

.. code-block:: text

    # PLATFORM.PUBMED
    ("health tracking" OR ("remote" AND "monitoring")) AND ("mobile application" OR "wearable device")

**Typical fix**: Use explicit parentheses to clarify operator precedence and avoid ambiguity in mixed AND/OR queries.
""",
    )
    OPERATOR_CAPITALIZATION = (
        "STRUCT_0002",
        "operator-capitalization",
        "Operators should be capitalized",
        """
**Problematic query**:

.. code-block:: text

    dHealth and mHealth

**Recommended query**:

.. code-block:: text

    dHealth AND mHealth

**Typical fix**: Capitalize the operator
""",
    )

    BOOLEAN_OPERATOR_READABILITY = (
        "STRUCT_0003",
        "boolean-operator-readability",
        "Boolean operator readability",
        """
**Problematic query**:

.. code-block:: text

    eHealth[ti] | mHealth[ti]

**Recommended query**:

.. code-block:: text

    eHealth[ti] OR mHealth[ti]
""",
    )
    INVALID_PROXIMITY_USE = (
        "STRUCT_0004",
        "invalid-proximity-use",
        "Invalid use of the proximity operator",
        """
Proximity operators must have a non-negative integer as the distance.

**Problematic query**:

.. code-block:: text

    "digital health"[tiab:~0.5]

**Recommended query**:

.. code-block:: text

    "digital health"[tiab:5]
""",
    )

    # -------------------------------------------------------
    # Term
    # -------------------------------------------------------

    NON_STANDARD_QUOTES = (
        "TERM_0001",
        "non-standard-quotes",
        "Non-standard quotes",
        """
**Problematic query**:

.. code-block:: text

    TS=“carbon”

**Recommended query**:

.. code-block:: text

    TS="carbon"

**Typical fix**: Replace non-standard quotes (e.g., “ ”) with standard ASCII quotes (").
""",
    )
    YEAR_FORMAT_INVALID = (
        "TERM_0002",
        "year-format-invalid",
        "Invalid year format.",
        """
**Problematic query**:

.. code-block:: text

    TI=term1 AND PY=20xy

**Recommended query**:

.. code-block:: text

    TI=term1 AND PY=2020

**Typical fix**: Use a valid numeric year format (e.g., 4-digit year).
""",
    )
    DOI_FORMAT_INVALID = (
        "TERM_0003",
        "doi-format-invalid",
        "Invalid DOI format.",
        """
**Problematic query**:

.. code-block:: text

    DO=12.1000/xyz

**Recommended query**:

.. code-block:: text

    DO=10.1000/xyz

**Typical fix**: Use a valid DOI format (e.g., starts with 10. followed by a numeric string and suffix).
""",
    )
    ISBN_FORMAT_INVALID = (
        "TERM_0004",
        "isbn-format-invalid",
        "Invalid ISBN format.",
        """
**Problematic query**:

.. code-block:: text

    IS=978-3-16-148410-0

**Recommended query**:

.. code-block:: text

    IS=978-3-16-148410-0

**Typical fix**: Use a valid ISBN-10 or ISBN-13 format (e.g., 10 or 13 digits, optionally with hyphens in correct positions).
""",
    )

    # -------------------------------------------------------
    # Web of Science
    # -------------------------------------------------------

    # Note: introduce this error for databases that have a limit on the number of operators
    # WOS: 49 operators refers to ALL Search Fields
    #     TOO_MANY_OPERATORS = (
    #         ["all"],
    #         "F1011",
    #         "too-many-operators",
    #         "Too many operators in the query",
    #         """
    # **Explanation:** The query contains too many logical operators (AND, OR, NOT) or proximity operators (NEAR, WITHIN).
    # """,  # Note: do not include a long example
    #   )
    TOO_MANY_TERMS = (
        "WOS_0001",
        "too-many-terms",
        "Too many search terms in the query",
        """
**Explanation:** The query contains too many search terms, which may lead to performance issues or exceed platform limits.

**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS
    # too many terms
    TI=(eHealth OR digital health OR telemedicine OR mHealth OR ...)

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS
    # split into multiple queries
    TI=(eHealth OR digital health OR telemedicine OR ...)
    TI=(mHealth OR telehealth OR ...)
""",  # Note: do not include a long example
    )
    NEAR_DISTANCE_TOO_LARGE = (
        "WOS_0002",
        "near-distance-too-large",
        "NEAR distance is too large (max: 15).",
        """
**Problematic query**:

.. code-block:: text

    TI=term1 NEAR/20 term2

**Recommended query**:

.. code-block:: text

    TI=term1 NEAR/15 term2

**Typical fix**: Reduce the NEAR distance to 15 or less.
""",
    )

    YEAR_WITHOUT_TERMS = (
        "WOS_0003",
        "year-without-terms",
        "A search for publication years must include at least another search term.",
        """
**Problematic query**:

.. code-block:: text

    PY=2000

**Recommended query**:

.. code-block:: text

    TI=term AND PY=2000

**Typical fix**: Combine the year filter with at least one other search term.
""",
    )

    IMPLICIT_NEAR_VALUE = (
        "WOS_0004",
        "implicit-near-value",
        "The value of NEAR operator is implicit",
        """
**Problematic query**:

.. code-block:: text

    A NEAR B

**Recommended query**:

.. code-block:: text

    A NEAR/15 B

**Typical fix**: The parser automatically sets NEAR values to 15 (default).
""",
    )

    YEAR_SPAN_VIOLATION = (
        "WOS_0005",
        "year-span-violation",
        "Year span must be five or less.",
        """
**Problematic query**:

.. code-block:: text

    A AND PY=2000-2020

**Recommended query**:

.. code-block:: text

    A AND PY=2015-2020

**Typical fix**: The parser automatically adjusts the year span to 5 years.
""",
    )

    WILDCARD_IN_YEAR = (
        "WOS_0006",
        "wildcard-in-year",
        "Wildcard characters (*, ?, $) not supported in year search.",
        """
**Problematic query**:

.. code-block:: text

    dHealth[ti] AND 200*[dp]

**Recommended query**:

.. code-block:: text

    dHealth[ti] AND 2000:2010[dp]

**Typical fix**: Replace with year range.
""",
    )
    WILDCARD_LEFT_SHORT_LENGTH = (
        "WOS_0007",
        "wildcard-left-short-length",
        "Left-hand wildcard must be followed by at least three characters.",
        """
**Problematic query**:

.. code-block:: text

    TI=*te

**Recommended query**:

.. code-block:: text

    TI=abc*te

**Typical fix**: Ensure the term before a left-hand wildcard (*) has at least three characters.
""",
    )
    WILDCARD_RIGHT_SHORT_LENGTH = (
        "WOS_0008",
        "wildcard-right-short-length",
        "Right-hand wildcard must preceded by at least three characters.",
        """
**Problematic query**:

.. code-block:: text

    TI=te*
    TS=ca*

**Recommended query**:

.. code-block:: text

    TI=tech*
    TS=cat*

**Typical fix**: Replace short wildcard prefix with at least three characters or use a more specific term.
""",
    )
    WILDCARD_AFTER_SPECIAL_CHAR = (
        "WOS_0009",
        "wildcard-after-special-char",
        "Wildcard cannot be preceded by special characters.",
        """
**Problematic query**:

.. code-block:: text

    TI=(term1 OR term2!*)

**Recommended query**:

.. code-block:: text

    TI=(term1 OR term2*)

**Typical fix**: Remove the special character before the wildcard or rephrase the query to avoid combining them.
""",
    )
    WILDCARD_STANDALONE = (
        "WOS_0010",
        "wildcard-standalone",
        "Wildcard cannot be standalone.",
        """
**Problematic query**:

.. code-block:: text

    TI=term1 AND "?"

**Recommended query**:

.. code-block:: text

    TI=term1

**Typical fix**: Replace the standalone wildcard with a complete search term or remove it entirely.
""",
    )

    WOS_WILDCARD_UNSUPPORTED = (
        "WOS_0011",
        "wildcard-unsupported",
        "Unsupported wildcard in search string.",
        """
**Problematic query**:

.. code-block:: text

   dHealth!

**Recommended query**:

.. code-block:: text

    dHealth

**Typical fix**:  Remove unsupported wildcard characters from the query.""",
    )

    WOS_INVALID_CHARACTER = (
        "WOS_0012",
        "invalid-character",
        "Search term contains invalid character",
        """
**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS
    "@digital-native"[ti]

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS
    "digital-native"[ti]

""",
    )

    # pylint: disable=too-many-arguments
    def __init__(self, code: str, label: str, message: str, docs: str) -> None:
        self.code = code
        self.label = label
        self.message = message
        self.docs = docs
