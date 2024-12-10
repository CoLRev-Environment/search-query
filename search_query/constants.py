#!/usr/bin/env python
"""Constants for search-query"""
# pylint: disable=too-few-public-methods
# pylint: disable=line-too-long
from enum import Enum

# noqa: E501


class PLATFORM(Enum):
    """Database identifier"""

    WOS = "wos"
    PUBMED = "pubmed"
    EBSCO = "ebsco"
    STRUCTURED = "structured"
    PRE_NOTATION = "pre_notation"


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
    TOPIC = "ts"
    LANGUAGE = "la"
    YEAR = "py"

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
        Fields.AUTHOR_KEYWORDS: "AU=",
        Fields.TITLE: "TI=",
        Fields.TOPIC: "TS=",
        Fields.LANGUAGE: "LA=",
        Fields.YEAR: "PY=",
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


class LinterMode:
    """Linter mode"""
    STRICT = 'strict'
    NONSTRICT = 'non-strict'

class WOSRegex:
    """Regex for WOS"""
    TERM_REGEX = r'\*?[\w-]+(?:[\*\$\?][\w-]*)*|"[^"]+"'
    OPERATOR_REGEX = r'\b(AND|and|OR|or|NOT|not|NEAR/\d{1,2}|near/\d{1,2}|NEAR|near)\b'
    SEARCH_FIELD_REGEX = r'\b\w{2}=|\b\w{3}='
    PARENTHESIS_REGEX = r'[\(\)]'
    SEARCH_FIELDS_REGEX = r'\b(?!and\b)[a-zA-Z]+(?:\s(?!and\b)[a-zA-Z]+)*'
    YEAR_REGEX = r"^\d{4}(-\d{4})?$"
