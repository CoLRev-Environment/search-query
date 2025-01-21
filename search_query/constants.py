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
    MESH_TERM = "mh"

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
        Fields.AUTHOR_KEYWORDS: "[au]",
        Fields.MESH_TERM: "[mh]"
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


class PubmedErrorCodes:
    """Error codes used by the Pubmed parser"""

    UNBALANCED_PARENTHESES = "F0002"
    MISSING_OPERATOR = "F0003"
    INVALID_BRACKET_USE = "F0004"
    INVALID_OPERATOR_POSITION = "F0005"
    INVALID_FIELD_POSITION = "F0006"
    EMPTY_PARENTHESES = "F0007"
    NESTED_NOT_QUERY = "F0008"

    FIELD_CONTRADICTION = "E0001"
    UNSUPPORTED_FIELD = "E0003"
    MISSING_QUERY_FIELD = "E0004"
    INVALID_PROXIMITY_DISTANCE = "E0005"
    INVALID_PROXIMITY_USE = "E0006"
    INVALID_PROXIMITY_SYNTAX = "E0007"
    INVALID_CHARACTER = "E0008"

    FIELD_REDUNDANT = "W0001"
    FIELD_NOT_SPECIFIED = "W0002"
    TERM_REDUNDANT = "W0003"


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
