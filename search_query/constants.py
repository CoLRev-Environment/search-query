#!/usr/bin/env python
"""Constants for search-query"""
# pylint: disable=too-few-public-methods
# pylint: disable=line-too-long
from enum import Enum

# noqa: E501


class PLATFORM(Enum):
    """Database identifier"""

    CROSSREF = "crossref"
    WOS = "wos"
    PUBMED = "pubmed"
    EBSCO = "ebsco"
    AISEL = "aisel"
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
    TOPIC = "ts"
    TEXT_WORDS = "tw"
    ABSTRACT = "ab"
    JOURNAL = "ta"
    AUTHOR = "au"
    AUTHOR_KEYWORDS = "ak"
    WOS_KEYWORDS_PLUS = "kp"
    DOI = "doi"
    ISBN_ISSN = "isbn"
    YEAR = "py"
    LANGUAGE = "la"
    PUBLISHER = "pubn"
    DOCUMENT_TYPE = "dt"
    MESH_NO_EXP = "mesh_no_exp"
    MESH = "mesh"
    MESH_MAJOR = "majr"
    RESEARCH_AREA = "su"
    WOS_CATEGORY = "wc"
    AFFILIATION = "affiliation"
    PII = "pii"
    BOOKACCESSION = "bookaccession"
    SUBHEADING = "sh"
    SUPPLEMENTARY_CONCEPT = "sc"
    PUBLICATION_TYPE = "pt"
    PHARMACOLOGICAL_ACTION = "pa"

    EBSCO_UNQUALIFIED = "EBSCO_UNQUALIFIED"

    SUBSET = "sb"  # pubmed filter

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
        Fields.AUTHOR: "AU=",
        Fields.AUTHOR_KEYWORDS: "AK=",
        Fields.DOI: "DO=",
        Fields.ISBN_ISSN: "IS=",
        Fields.TITLE: "TI=",
        Fields.YEAR: "PY=",
        Fields.TOPIC: "TS=",
        Fields.LANGUAGE: "LA=",
        Fields.DOCUMENT_TYPE: "DT=",
        Fields.WOS_KEYWORDS_PLUS: "KP=",
        Fields.RESEARCH_AREA: "SU=",
        Fields.WOS_CATEGORY: "WC=",
        Fields.AFFILIATION: "AD=",
        # Fields.XXX: "AI=",
        # Fields.XXX: "GP=",
        # Fields.XXX: "ED=",
        # Fields.XXX: "SO=",
        # Fields.XXX: "CF=",
        # Fields.XXX: "OG=",
        # Fields.XXX: "OO=",
        # Fields.XXX: "SG=",
        # Fields.XXX: "SA=",
        # Fields.XXX: "CI=",
        # Fields.XXX: "PS=",
        # Fields.XXX: "CU=",
        # Fields.XXX: "ZP=",
        # Fields.XXX: "FO=",
        # Fields.XXX: "FG=",
        # Fields.XXX: "FD=",
        # Fields.XXX: "FT=",
        # Fields.XXX: "UT=",
        # Fields.XXX: "PMID=",
        # Fields.XXX: "DOP=",
        # Fields.XXX: "LD=",
        # Fields.XXX: "PUBL=",
        # Fields.XXX: "FPY=",
        # Fields.XXX: "EAY=",
        # Fields.XXX: "SDG=",
    },
    # fields from https://pubmed.ncbi.nlm.nih.gov/help/
    PLATFORM.PUBMED: {
        Fields.ALL: "[all]",
        Fields.TITLE: "[ti]",
        Fields.ABSTRACT: "[ab]",
        Fields.AUTHOR: "[au]",
        Fields.AUTHOR_KEYWORDS: "[ot]",
        Fields.ISBN_ISSN: "[is]",
        Fields.YEAR: "[dp]",
        Fields.LANGUAGE: "[la]",
        Fields.MESH_NO_EXP: "[mesh:noexp]",
        Fields.MESH: "[mh]",
        Fields.MESH_MAJOR: "[majr]",
        Fields.SUBSET: "[sb]",
        Fields.AFFILIATION: "[affiliation]",
        Fields.TEXT_WORDS: "[tw]",
        Fields.SUBHEADING: "[sh]",
        Fields.PUBLICATION_TYPE: "[pt]",
        Fields.PHARMACOLOGICAL_ACTION: "[pa]",
        Fields.JOURNAL: "[ta]",
    },
    # fields from https://connect.ebsco.com/s/article/Searching-with-Field-Codes?language=en_US
    PLATFORM.EBSCO: {
        Fields.TITLE: "TI ",
    },
    PLATFORM.CROSSREF: {
        Fields.ALL: "query",  # TODO : or query.bibliographic ??
        Fields.TITLE: "query.title",
        Fields.AUTHOR: "query.author",
    },
}

# For convenience, modules can use the following to translate fields to a PLATFORM
PLATFORM_FIELD_TRANSLATION_MAP = {
    PLATFORM: {v: k for k, v in fields.items()}
    for PLATFORM, fields in PLATFORM_FIELD_MAP.items()
}

PLATFORM_COMBINED_FIELDS_MAP = {
    PLATFORM.PUBMED: {
        "[tiab]": [Fields.TITLE, Fields.ABSTRACT],
        "[aid]": [Fields.DOI, Fields.PII, Fields.BOOKACCESSION],
    },
    PLATFORM.EBSCO: {
        # https://connect.ebsco.com/s/article/What-is-an-unqualified-search?language=en_US
        "EBSCO_UNQUALIFIED": [
            Fields.AUTHOR,
            Fields.RESEARCH_AREA,
            Fields.AUTHOR_KEYWORDS,
            Fields.ABSTRACT,
        ],
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
