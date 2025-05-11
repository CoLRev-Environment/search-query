#!/usr/bin/env python3
"""Constants for Web-of-Science."""
import re
from copy import deepcopy

from search_query.constants import Fields

# https://webofscience.help.clarivate.com/en-us/Content/wos-core-collection/woscc-search-field-tags.htm


# Mapping from standard WOS syntax to generic Fields
SYNTAX_GENERIC_MAP = {
    "ALL=": {Fields.ALL},
    "AB=": {Fields.ABSTRACT},
    "TI=": {Fields.TITLE},
    "TS=": {Fields.TOPIC},
    "LA=": {Fields.LANGUAGE},
    "PY=": {Fields.YEAR},
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

VALID_FIELDS_REGEX = re.compile(
    "|".join(v.pattern for v in PREPROCESSING_MAP.values()), flags=re.IGNORECASE  # type: ignore
)


def map_to_standard(syntax_str: str) -> str:
    """Normalize search field string to a standard WOS field syntax."""
    for standard_key, variation_regex in PREPROCESSING_MAP.items():
        if variation_regex.match(syntax_str):  # type: ignore
            return standard_key
    raise ValueError(f"Search field not recognized: {syntax_str}")


def map_search_field(field_value: str) -> set:
    """Translate a search field string to a generic set of Fields."""
    field_value = field_value.strip().lower()
    field_value = map_to_standard(field_value.upper())
    for key, value in SYNTAX_GENERIC_MAP.items():
        if field_value.upper() == key:
            return deepcopy(value)
    raise ValueError(f"Field {field_value} not supported by Web of Science")


def generic_search_field_set_to_syntax_set(generic_search_field_set: set) -> set:
    """Convert a set of generic search fields to WOS syntax strings."""
    syntax_set = set()
    for key, value in SYNTAX_GENERIC_MAP.items():
        if generic_search_field_set == value:
            syntax_set.add(key)
    if not syntax_set:
        raise ValueError(
            f"Generic search field set {generic_search_field_set} not supported by WOS"
        )
    return syntax_set


SEARCH_FIELD_GENERAL_TO_GENERIC_MAP = {
    "All Fields": {Fields.ALL},
    "Topic": {Fields.TOPIC},
    "Title": {Fields.TITLE},
    "Author": {Fields.AUTHOR},
    "Publication Titles": {Fields.PUBLICATION_NAME},
    "Year Published": {Fields.YEAR},
    "Affiliation": {Fields.AFFILIATION},
    "Funding Agency": {Fields.FUNDING_AGENCY},
    "Publisher": {Fields.PUBLISHER},
    "Publiation Date": {Fields.PUBLICATION_DATE},
    "Abstract": {Fields.ABSTRACT},
    "Accession Number": {Fields.ACCESSION_NUMBER},
    "Address": {Fields.ADDRESS},
    "Author Identifiers": {Fields.AUTHOR_IDENTIFIERS},
    "Author Keywords": {Fields.AUTHOR_KEYWORDS},
    "Conference": {Fields.CONFERENCE},
    "Document Type": {Fields.PUBLICATION_TYPE},
    "DOI": {Fields.DOI},
    "Editor": {Fields.EDITOR},
    "Grant Number": {Fields.GRANT_NUMBER},
    "Group Author": {Fields.GROUP_AUTHOR},
    "Keywords Plus": {Fields.KEYWORDS_PLUS},
    "Language": {Fields.LANGUAGE},
    "PubMed ID": {Fields.PUBMED_ID},
    "Web of Science Categories": {Fields.WEB_OF_SCIENCE_CATEGORY},
}


def map_search_field_general_to_generic(
    search_field: str,
) -> set:
    """Map a search field to a set of generic fields."""
    search_field = search_field.strip()
    if search_field in SEARCH_FIELD_GENERAL_TO_GENERIC_MAP:
        return SEARCH_FIELD_GENERAL_TO_GENERIC_MAP[search_field]
    raise ValueError(f"Search field {search_field} not supported by WOS")
