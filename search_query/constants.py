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
    UNKNOWN = "UNKNOWN"


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
    TOPIC = "ts"
    LANGUAGE = "la"
    YEAR = "py"
    ADDRESS = "ad"
    AUTHOR_IDENTIFIERS = "ai"
    AUTHOR_KEYWORDS = "ak"
    AUTHOR = "au"
    CONFERENCE = "cf"
    CITY = "ci"
    COUNTRY_REGION = "cu"
    DOI = "do"
    EDITOR = "ed"
    GRANT_NUMBER = "fg"
    FUNDING_AGENCY = "fo"
    FUNDING_TEXT = "ft"
    GROUP_AUTHOR = "gp"
    ISSN_ISBN = "is"
    KEYWORDS_PLUS = "kp"
    ORGANIZATION_ENHANCED = "og"
    ORGANIZATION = "oo"
    PUBMED_ID = "pmid"
    PROVINCE_STATE = "ps"
    STREET_ADDRESS = "sa"
    SUBORGANIZATION = "sg"
    PUBLICATION_NAME = "so"
    RESEARCH_AREA = "su"
    ACCESSION_NUMBER = "ut"
    WEB_OF_SCIENCE_CATEGORY = "wc"
    ZIP_POSTAL_CODE = "zp"
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
        Fields.TOPIC: "TS=",
        Fields.LANGUAGE: "LA=",
        Fields.YEAR: "PY=",
        Fields.ADDRESS: "AD=",
        Fields.AUTHOR_IDENTIFIERS: "AI=",
        Fields.AUTHOR_KEYWORDS: "AK=",
        Fields.AUTHOR: "AU=",
        Fields.CONFERENCE: "CF=",
        Fields.CITY: "CI=",
        Fields.COUNTRY_REGION: "CU=",
        Fields.DOI: "DO=",
        Fields.EDITOR: "ED=",
        Fields.GRANT_NUMBER: "FG=",
        Fields.FUNDING_AGENCY: "FO=",
        Fields.FUNDING_TEXT: "FT=",
        Fields.GROUP_AUTHOR: "GP=",
        Fields.ISSN_ISBN: "IS=",
        Fields.KEYWORDS_PLUS: "KP=",
        Fields.ORGANIZATION_ENHANCED: "OG=",
        Fields.ORGANIZATION: "OO=",
        Fields.PUBMED_ID: "PMID=",
        Fields.PROVINCE_STATE: "PS=",
        Fields.STREET_ADDRESS: "SA=",
        Fields.SUBORGANIZATION: "SG=",
        Fields.PUBLICATION_NAME: "SO=",
        Fields.RESEARCH_AREA: "SU=",
        Fields.ACCESSION_NUMBER: "UT=",
        Fields.WEB_OF_SCIENCE_CATEGORY: "WC=",
        Fields.ZIP_POSTAL_CODE: "ZP=",
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


class LinterMode:
    """Linter mode"""

    STRICT = "strict"
    NONSTRICT = "non-strict"


class WOSSearchFieldList:
    """List of search fields"""

    # Define lists for all search fields
    abstract_list = [
        "AB=",
        "Abstract",
        "ab=",
        "abstract=",
        "ab",
        "abstract",
        "AB",
        "ABSTRACT",
    ]
    language_list = [
        "LA=",
        "Languages",
        "la=",
        "language=",
        "la",
        "language",
        "LA",
        "LANGUAGE",
    ]
    address_list = [
        "AD=",
        "Address",
        "ad=",
        "address=",
        "ad",
        "address",
        "AD",
        "ADDRESS",
    ]
    all_fields_list = [
        "ALL=",
        "All Fields",
        "all=",
        "all fields=",
        "all",
        "all fields",
        "ALL",
        "ALL FIELDS",
    ]
    author_identifiers_list = [
        "AI=",
        "Author Identifiers",
        "ai=",
        "author identifiers=",
        "ai",
        "author identifiers",
        "AI",
        "AUTHOR IDENTIFIERS",
    ]
    author_keywords_list = [
        "AK=",
        "Author Keywords",
        "ak=",
        "author keywords=",
        "ak",
        "author keywords",
        "AK",
        "AUTHOR KEYWORDS",
    ]
    author_list = ["AU=", "Author", "au=", "author=", "au", "author", "AU", "AUTHOR"]
    conference_list = [
        "CF=",
        "Conference",
        "cf=",
        "conference=",
        "cf",
        "conference",
        "CF",
        "CONFERENCE",
    ]
    city_list = ["CI=", "City", "ci=", "city=", "ci", "city", "CI", "CITY"]
    country_region_list = [
        "CU=",
        "Country/Region",
        "cu=",
        "country/region=",
        "cu",
        "country/region",
        "CU",
        "COUNTRY/REGION",
    ]
    doi_list = ["DO=", "DOI", "do=", "doi=", "do", "doi", "DO", "DOI"]
    editor_list = ["ED=", "Editor", "ed=", "editor=", "ed", "editor", "ED", "EDITOR"]
    grant_number_list = [
        "FG=",
        "Grant Number",
        "fg=",
        "grant number=",
        "fg",
        "grant number",
        "FG",
        "GRANT NUMBER",
    ]
    funding_agency_list = [
        "FO=",
        "Funding Agency",
        "fo=",
        "funding agency=",
        "fo",
        "funding agency",
        "FO",
        "FUNDING AGENCY",
    ]
    funding_text_list = [
        "FT=",
        "Funding Text",
        "ft=",
        "funding text=",
        "ft",
        "funding text",
        "FT",
        "FUNDING TEXT",
    ]
    group_author_list = [
        "GP=",
        "Group Author",
        "gp=",
        "group author=",
        "gp",
        "group author",
        "GP",
        "GROUP AUTHOR",
    ]
    issn_isbn_list = [
        "IS=",
        "ISSN/ISBN",
        "is=",
        "issn/isbn=",
        "is",
        "issn/isbn",
        "IS",
        "ISSN/ISBN",
    ]
    keywords_plus_list = [
        "KP=",
        "Keywords Plus®",
        "kp=",
        "keywords plus=",
        "kp",
        "keywords plus",
        "KP",
        "KEYWORDS PLUS",
    ]
    organization_enhanced_list = [
        "OG=",
        "Organization - Enhanced",
        "og=",
        "organization - enhanced=",
        "og",
        "organization - enhanced",
        "OG",
        "ORGANIZATION - ENHANCED",
    ]
    organization_list = [
        "OO=",
        "Organization",
        "oo=",
        "organization=",
        "oo",
        "organization",
        "OO",
        "ORGANIZATION",
    ]
    pubmed_id_list = [
        "PMID=",
        "PubMed ID",
        "pmid=",
        "pubmed id=",
        "pmid",
        "pubmed id",
        "PMID",
        "PUBMED ID",
    ]
    province_state_list = [
        "PS=",
        "Province/State",
        "ps=",
        "province/state=",
        "ps",
        "province/state",
        "PS",
        "PROVINCE/STATE",
    ]
    year_published_list = [
        "PY=",
        "Year Published",
        "py=",
        "year published=",
        "py",
        "year published",
        "PY",
        "YEAR PUBLISHED",
        "Publication Year",
        "publication year",
        "PUBLICATION YEAR",
        "PUBLICATION YEAR",
    ]
    street_address_list = [
        "SA=",
        "Street Address",
        "sa=",
        "street address=",
        "sa",
        "street address",
        "SA",
        "STREET ADDRESS",
    ]
    suborganization_list = [
        "SG=",
        "Suborganization",
        "sg=",
        "suborganization=",
        "sg",
        "suborganization",
        "SG",
        "SUBORGANIZATION",
    ]
    publication_name_list = [
        "SO=",
        "Publication Name",
        "so=",
        "publication name=",
        "so",
        "publication name",
        "SO",
        "PUBLICATION NAME",
    ]
    research_area_list = [
        "SU=",
        "Research Area",
        "su=",
        "research area=",
        "su",
        "research area",
        "SU",
        "RESEARCH AREA",
    ]
    title_list = ["TI=", "Title", "ti=", "title=", "ti", "title", "TI", "TITLE"]
    topic_list = [
        "TS=",
        "Topic",
        "ts=",
        "topic=",
        "ts",
        "topic",
        "TS",
        "TOPIC",
        "Topic Search",
        "Topic TS",
    ]
    accession_number_list = [
        "UT=",
        "Accession Number",
        "ut=",
        "accession number=",
        "ut",
        "accession number",
        "UT",
        "ACCESSION NUMBER",
    ]
    web_of_science_category_list = [
        "WC=",
        "Web of Science Category",
        "wc=",
        "web of science category=",
        "wc",
        "web of science category",
        "WC",
        "WEB OF SCIENCE CATEGORY",
    ]
    zip_postal_code_list = [
        "ZP=",
        "Zip/Postal Code",
        "zp=",
        "zip/postal code=",
        "zp",
        "zip/postal code",
        "ZP",
        "ZIP/POSTAL CODE",
    ]

    search_field_dict = {
        "AB=": abstract_list,
        "AD=": address_list,
        "ALL=": all_fields_list,
        "AI=": author_identifiers_list,
        "AK=": author_keywords_list,
        "AU=": author_list,
        "CF=": conference_list,
        "CI=": city_list,
        "CU=": country_region_list,
        "DO=": doi_list,
        "ED=": editor_list,
        "FG=": grant_number_list,
        "FO=": funding_agency_list,
        "FT=": funding_text_list,
        "GP=": group_author_list,
        "IS=": issn_isbn_list,
        "KP=": keywords_plus_list,
        "LA=": language_list,
        "OG=": organization_enhanced_list,
        "OO=": organization_list,
        "PMID=": pubmed_id_list,
        "PS=": province_state_list,
        "PY=": year_published_list,
        "SA=": street_address_list,
        "SG=": suborganization_list,
        "SO=": publication_name_list,
        "SU=": research_area_list,
        "TI=": title_list,
        "TS=": topic_list,
        "UT=": accession_number_list,
        "WC=": web_of_science_category_list,
        "ZP=": zip_postal_code_list,
    }


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
    UNMATCHED_OPENING_PARENTHESIS = (
        ["all"],
        "F1002",
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
        "F1003",
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
    INVALID_TOKEN_SEQUENCE = (
        [PLATFORM.EBSCO],
        "F1004",
        "invalid-token-sequence",
        "The sequence of tokens is invalid "
        "([token_type] followed by [token_type] is not allowed)",
        "",
    )
    INVALID_OPERATOR_POSITION = (
        [PLATFORM.PUBMED],
        "F1006",
        "invalid-operator-position",
        "Invalid operator position",
        "",
    )
    INVALID_SEARCH_FIELD_POSITION = (
        [PLATFORM.PUBMED],
        "F1007",
        "invalid-search-field-position",
        "Search field tags should directly follow search terms",
        "",
    )
    NESTED_NOT_QUERY = (
        [PLATFORM.PUBMED],
        "F1008",
        "nested-not-query",
        "Nesting of NOT operator is not supported for this database",
        "",
    )
    EMPTY_PARENTHESES = (
        [PLATFORM.PUBMED],
        "F1009",
        "empty-parentheses",
        "Query contains empty parentheses",
        "",
    )
    # TODO : consolidate with INVALID_TOKEN_SEQUENCE (EBSCO) is non-fatal?!
    INVALID_TOKEN_SEQUENCE_TWO_SEARCH_FIELDS = (
        [PLATFORM.EBSCO],
        "F1010",
        "invalid-token-sequence-two-search-fields",
        "Invalid token sequence: two search fields in a row.",
        "",
    )
    INVALID_TOKEN_SEQUENCE_TWO_OPERATORS = (
        [PLATFORM.EBSCO],
        "F1011",
        "invalid-token-sequence-two-operators",
        "Invalid token sequence: two operators in a row.",
        "",
    )
    # Note : merged MISSING_OPERATOR with:
    INVALID_TOKEN_SEQUENCE_MISSING_OPERATOR = (
        ["all", PLATFORM.WOS],
        "F1012",
        "invalid-token-sequence-missing-operator",
        "Invalid token sequence: missing operator.",
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
        "",
    )
    WILDCARD_LEFT_SHORT_LENGTH = (
        [PLATFORM.WOS],
        "F2004",
        "wildcard-left-short-length",
        "Left-hand wildcard must be preceded by at least three characters.",
        "",
    )
    WILDCARD_AFTER_SPECIAL_CHAR = (
        [PLATFORM.WOS],
        "F2005",
        "wildcard-after-special-char",
        "Wildcard cannot be preceded by special characters.",
        "",
    )
    WILDCARD_STANDALONE = (
        [PLATFORM.WOS],
        "F2006",
        "wildcard-standalone",
        "Wildcard cannot be standalone.",
        "",
    )
    NEAR_DISTANCE_TOO_LARGE = (
        [PLATFORM.WOS],
        "F2007",
        "near-distance-too-large",
        "NEAR distance is too large (max: 15).",
        "",
    )
    ISBN_FORMAT_INVALID = (
        [PLATFORM.WOS],
        "F2008",
        "isbn-format-invalid",
        "Invalid ISBN format.",
        "",
    )
    DOI_FORMAT_INVALID = (
        [PLATFORM.WOS],
        "F2009",
        "doi-format-invalid",
        "Invalid DOI format.",
        "",
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
        "",
    )

    # -------------------------------------------------------
    # Errors (prefix: E)
    # -------------------------------------------------------
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
        "",
    )
    SEARCH_FIELD_EXTRACTED = (
        ["all"],
        "W0002",
        "search-field-extracted",
        "Recommend explicitly specifying the search field in the string",
        "",
    )
    # TODO : equals SEARCH_FIELD_MISSING ??
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
        "Operator changed at the same level "
        "(currently relying on implicit operator precedence, "
        "explicit parentheses are recommended)",
        "",
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

    def is_error(self) -> bool:
        """Check if error is an error"""
        return self.code.startswith("E")

    def is_warning(self) -> bool:
        """Check if error is a warning"""
        return self.code.startswith("W")
