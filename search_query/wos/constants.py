#!/usr/bin/env python3
"""Constants for Web-of-Science."""
from __future__ import annotations

import re
from copy import deepcopy

from search_query.constants import Fields

# https://webofscience.help.clarivate.com/en-us/Content/wos-core-collection/woscc-field-tags.htm


# Mapping from standard WOS syntax to generic Fields
SYNTAX_GENERIC_MAP = {
    "ALL=": {Fields.ALL},
    "AB=": {Fields.ABSTRACT},
    "TI=": {Fields.TITLE},
    "TS=": {
        Fields.TITLE,
        Fields.ABSTRACT,
        Fields.AUTHOR_KEYWORDS,
        Fields.KEYWORDS_PLUS,
    },
    "LA=": {Fields.LANGUAGE},
    "PY=": {Fields.YEAR_PUBLICATION},
    "AD=": {Fields.ADDRESS},
    "AI=": {Fields.AUTHOR_IDENTIFIERS},
    "AK=": {Fields.AUTHOR_KEYWORDS},
    "AU=": {Fields.AUTHOR},
    "CF=": {Fields.CONFERENCE},
    "CI=": {Fields.CITY},
    "CU=": {Fields.COUNTRY_REGION},
    "DO=": {Fields.DOI},
    "ED=": {Fields.EDITOR},
    "FG=": {Fields.GRANT_NUMBER},
    "FO=": {Fields.FUNDING_AGENCY},
    "FT=": {Fields.FUNDING_TEXT},
    "GP=": {Fields.GROUP_AUTHOR},
    "IS=": {Fields.ISSN_ISBN},
    "KP=": {Fields.KEYWORDS_PLUS},
    "OG=": {Fields.ORGANIZATION_ENHANCED},
    "OO=": {Fields.ORGANIZATION},
    "PMID=": {Fields.PUBMED_ID},
    "PS=": {Fields.PROVINCE_STATE},
    "SA=": {Fields.STREET_ADDRESS},
    "SG=": {Fields.SUBORGANIZATION},
    "SO=": {Fields.PUBLICATION_NAME},
    "SU=": {Fields.RESEARCH_AREA},
    "UT=": {Fields.ACCESSION_NUMBER},
    "WC=": {Fields.WEB_OF_SCIENCE_CATEGORY},
    "ZP=": {Fields.ZIP_POSTAL_CODE},
}


# Variants of syntax strings to normalize to standard WOS fields
# Note: instead of lising capitlized options, use re.IGNORECASE in matching
# YEAR_PUBLISHED_FIELD_REGEX = r"py=|year published="
# ISSN_ISBN_FIELD_REGEX = r"is=|issn/isbn="
# DOI_FIELD_REGEX = r"do=|doi="

YEAR_PUBLISHED_FIELD_REGEX: re.Pattern = re.compile(
    r"py=|year published=", re.IGNORECASE
)
ISSN_ISBN_FIELD_REGEX: re.Pattern = re.compile(r"is=|issn/isbn=", re.IGNORECASE)
DOI_FIELD_REGEX: re.Pattern = re.compile(r"do=|doi=", re.IGNORECASE)
_RAW_PREPROCESSING_MAP = {
    "AB=": r"ab=|abstract=",
    "LA=": r"la=|language=",
    "AD=": r"ad=|address=",
    "ALL=": r"all=|all fields=",
    "AI=": r"ai=|author identifiers=",
    "AK=": r"ak=|author keywords=",
    "AU=": r"au=|author=",
    "CF=": r"cf=|conference=",
    "CI=": r"ci=|city=",
    "CU=": r"cu=|country/region=",
    "DO=": DOI_FIELD_REGEX,
    "ED=": r"ed=|editor=",
    "FG=": r"fg=|grant number=",
    "FO=": r"fo=|funding agency=",
    "FT=": r"ft=|funding text=",
    "GP=": r"gp=|group author=",
    "IS=": ISSN_ISBN_FIELD_REGEX,
    "KP=": r"kp=|keywords plus=",
    "OG=": r"og=|organization - enhanced=",
    "OO=": r"oo=|organization=",
    "PMID=": r"pmid=|pubmed id=",
    "PS=": r"ps=|province/state=",
    "PY=": YEAR_PUBLISHED_FIELD_REGEX,
    "SA=": r"sa=|street address=",
    "SG=": r"sg=|suborganization=",
    "SO=": r"so=|publication name=",
    "SU=": r"su=|research area=",
    "TI=": r"ti=|title=",
    "TS=": r"ts=|topic=",
    "UT=": r"ut=|accession number=",
    "WC=": r"wc=|web of science category=",
    "ZP=": r"zp=|zip/postal code=",
}

PREPROCESSING_MAP = {
    k: re.compile(v, re.IGNORECASE) if isinstance(v, str) else v
    for k, v in _RAW_PREPROCESSING_MAP.items()
}

VALID_fieldS_REGEX = re.compile(
    "|".join(v.pattern for v in PREPROCESSING_MAP.values()), flags=re.IGNORECASE  # type: ignore
)


def map_to_standard(syntax_str: str) -> str:
    """Normalize search field string to a standard WOS field syntax."""
    for standard_key, variation_regex in PREPROCESSING_MAP.items():
        if variation_regex.match(syntax_str):  # type: ignore
            return standard_key
    raise ValueError(f"Search field not recognized: {syntax_str}")


def syntax_str_to_generic_field_set(field_value: str) -> set:
    """Translate a search field string to a generic set of Fields."""
    field_value = field_value.strip().lower()
    field_value = map_to_standard(field_value.upper())
    for key, value in SYNTAX_GENERIC_MAP.items():
        if field_value.upper() == key:
            return deepcopy(value)
    raise ValueError(
        f"Field {field_value} not supported by Web of Science"
    )  # pragma: no cover


def generic_field_to_syntax_field(generic_field: str) -> str:
    """Convert a set of generic search fields to a set of syntax strings."""

    for key, value in SYNTAX_GENERIC_MAP.items():
        if {generic_field} == value:
            return key

    for key, value in SYNTAX_GENERIC_MAP.items():
        if {generic_field} & value:
            return key

    raise ValueError(  # pragma: no cover
        f"Generic search field set {generic_field} " "not supported by WOS"
    )


field_GENERAL_TO_SYNTAX_MAP = {
    "All Fields": "ALL=",
    "Topic": "TS=",
    "Title": "TI=",
    "Author": "AU=",
    "Publication Titles": "SO=",
    "Year Published": "PY=",
    "Affiliation": "AD=",
    "Funding Agency": "FO=",
    # "Publisher": "PU=", # deprecated ?
    # "Publiation Date": "PY=", # deprecated ?
    "Abstract": "AB=",
    "Accession Number": "UT=",
    "Address": "AD=",
    "Author Identifiers": "AI=",
    "Author Keywords": "AK=",
    "Conference": "CF=",
    "Document Type": "DT=",
    "DOI": "DO=",
    "Editor": "ED=",
    "Grant Number": "FG=",
    "Group Author": "GP=",
    "Keywords Plus": "KP=",
    "Language": "LA=",
    "PubMed ID": "PMID=",
    "Web of Science Categories": "WC=",
}


def field_general_to_syntax(
    field: str,
) -> str:
    """Map the general search field to the standard syntax of WOS."""
    field = field.strip()
    if field in field_GENERAL_TO_SYNTAX_MAP:
        return field_GENERAL_TO_SYNTAX_MAP[field]

    raise ValueError(f"Search field {field} not supported by WOS")  # pragma: no cover
