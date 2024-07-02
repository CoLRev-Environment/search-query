#!/usr/bin/env python
"""Constants for search-query"""
# pylint: disable=too-few-public-methods
# https://pubmed.ncbi.nlm.nih.gov/help/
# https://webofscience.help.clarivate.com/en-us/Content/wos-core-collection/woscc-search-field-tags.htm


class Fields:
    """Search fields"""

    ALL = "all"
    TEXT_WORDS = "tw"
    ABSTRACT = "ab"
    TITLE_ABSTRACT = "tiab"
    AUTHOR = "au"
    AUTHOR_KEYWORDS = "ak"
    WOS_KEYWORDS_PLUS = "kp"
    DOI = "doi"
    ISBN_ISSN = "isbn"
    TITLE = "ti"
    YEAR = "py"
    TOPIC = "ts"
    LANGUAGE = "la"
    PUBLISHER = "pubn"
    DOCUMENT_TYPE = "dt"
    MESH_NO_EXP = "mesh_no_exp"
    MESH = "mesh"
    RESEARCH_AREA = "su"
    WOS_CATEGORY = "wc"
    AFFILIATION = "affiliation"

    SUBSET = "sb"  # pubmed filter


class Syntax:
    """Database syntax"""

    WOS = "wos"
    PUBMED = "pubmed"


SYNTAX_FIELD_MAP = {
    # field tags from https://www.webofscience.com/wos/woscc/advanced-search
    Syntax.WOS: {
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
    Syntax.PUBMED: {
        Fields.ALL: "[all]",
        Fields.TITLE: "[ti]",
        Fields.ABSTRACT: "[ab]",
        Fields.AUTHOR: "[au]",
        Fields.AUTHOR_KEYWORDS: "[ot]",
        Fields.DOI: "[aid]",  # TODO
        Fields.ISBN_ISSN: "[is]",
        Fields.YEAR: "[dp]",
        Fields.TOPIC: "[mh]",  # TODO
        Fields.LANGUAGE: "[la]",
        Fields.MESH_NO_EXP: "[mesh:noexp]",
        Fields.MESH: "[mesh]",
        Fields.SUBSET: "[sb]",
        Fields.AFFILIATION: "[affiliation]",
        Fields.TEXT_WORDS: "[tw]",
    },
}

# For convenience, we can use the following to translate fields to syntax
SYNTAX_FIELD_TRANSLATION_MAP = {
    syntax: {v: k for k, v in fields.items()}
    for syntax, fields in SYNTAX_FIELD_MAP.items()
}

# TODO : implement combined fields
SYNTAX_COMBINED_FIELDS_MAP = {
    Syntax.PUBMED: {
        "[tiab]": [Fields.TITLE, Fields.ABSTRACT],
    }
}


class Operators:
    """Operators"""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    NEAR = "NEAR"


class Colors:
    """Colors for CLI printing"""

    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"
