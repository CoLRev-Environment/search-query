#!/usr/bin/env python3
"""Constants for EBSCO."""
from __future__ import annotations

import re
from copy import deepcopy

from search_query.constants import Fields

# pylint: disable=too-few-public-methods
# pylint: disable=duplicate-code

# fields from
# https://connect.ebsco.com/s/article/Searching-with-Field-Codes

SYNTAX_GENERIC_MAP = {
    "TI": {Fields.TITLE},
    "AB": {Fields.ABSTRACT},
    "TP": {Fields.TOPIC},
    "TX": {Fields.ALL},
    "AU": {Fields.AUTHOR},
    "SU": {Fields.SUBJECT_TERMS},
    "SO": {Fields.SOURCE},
    "IS": {Fields.ISSN},
    "IB": {Fields.ISBN},
    "LA": {Fields.LANGUAGE},
    "KW": {Fields.AUTHOR_KEYWORDS, Fields.KEYWORDS},
    "ZW": {Fields.AUTHOR_KEYWORDS, Fields.KEYWORDS},
    "DE": {Fields.DESCRIPTORS, Fields.AUTHOR_KEYWORDS},
    "MH": {Fields.MESH_TERM},
    "ZY": {Fields.COUNTRY_REGION},
    "ZU": {Fields.SUBJECT_TERMS},
    "PT": {Fields.PUBLICATION_TYPE},
}

_RAW_PREPROCESSING_MAP = {
    "TI": r"TI",
    "AB": r"AB",
    "TP": r"TP",
    "TX": r"TX",
    "AU": r"AU",
    "SU": r"SU",
    "SO": r"SO",
    "IS": r"IS",
    "IB": r"IB",
    "LA": r"LA",
    "KW": r"KW",
    "DE": r"DE",
    "MH": r"MH",
    "ZY": r"ZY",
    "ZU": r"ZU",
    "PT": r"PT",
}
# Note: lower-case fields return different results
PREPROCESSING_MAP = {k: re.compile(v) for k, v in _RAW_PREPROCESSING_MAP.items()}

VALID_fieldS_REGEX = re.compile(
    "|".join(v.pattern for v in PREPROCESSING_MAP.values()), flags=re.IGNORECASE  # type: ignore
)


def map_to_standard(syntax_str: str) -> str:
    """Map a syntax string to a standard syntax string."""
    for standard_key, variation_regex in PREPROCESSING_MAP.items():
        if re.match(variation_regex, syntax_str):
            return standard_key
    raise ValueError


def syntax_str_to_generic_field_set(field_value: str) -> set:
    """Translate a search field"""

    # Convert search fields to their abbreviated forms (e.g. "[title] -> "[ti]")
    field_value = map_to_standard(field_value)

    # Convert search fields to default field constants
    for key, value in SYNTAX_GENERIC_MAP.items():
        if field_value == key:
            return deepcopy(value)

    raise ValueError(f"Field {field_value} not supported by EBSCO")  # pragma: no cover


def generic_field_to_syntax_field(generic_field: str) -> str:
    """Convert a set of generic search fields to a set of syntax strings."""

    for key, value in SYNTAX_GENERIC_MAP.items():
        if {generic_field} == value:
            return key

    for key, value in SYNTAX_GENERIC_MAP.items():
        if {generic_field} & value:
            return key

    raise ValueError(  # pragma: no cover
        f"Generic search field set {generic_field} not supported by EBSCO"
    )
