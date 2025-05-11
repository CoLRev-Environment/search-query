#!/usr/bin/env python3
"""Constants for EBSCO."""
# pylint: disable=too-few-public-methods
import re
from copy import deepcopy

from search_query.constants import Fields


# fields from
# https://connect.ebsco.com/s/article/Searching-with-Field-Codes

SYNTAX_GENERIC_MAP = {
    "TI": {Fields.TITLE},
    "AB": {Fields.ABSTRACT},
    "TP": {Fields.TOPIC},
    "TX": {Fields.ALL},
    "AU": {Fields.AUTHOR_KEYWORDS},
    "SU": {Fields.SUBJECT_TERMS},
    "SO": {Fields.SOURCE},
    "IS": {Fields.ISSN},
    "IB": {Fields.ISBN},
    "LA": {Fields.LANGUAGE},
    "KW": {Fields.KEYWORDS},
    "DE": {Fields.DESCRIPTORS},
}


# TODO : test whether lower case is accepted
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
}

PREPROCESSING_MAP = {
    k: re.compile(v, re.IGNORECASE) for k, v in _RAW_PREPROCESSING_MAP.items()
}

VALID_FIELDS_REGEX = re.compile(
    "|".join(v.pattern for v in PREPROCESSING_MAP.values()), flags=re.IGNORECASE  # type: ignore
)


def map_to_standard(syntax_str: str) -> str:
    """Map a syntax string to a standard syntax string."""
    for standard_key, variation_regex in PREPROCESSING_MAP.items():
        if re.match(variation_regex, syntax_str, flags=re.IGNORECASE):
            return standard_key
    raise ValueError


def map_search_field(field_value: str) -> set:
    """Translate a search field"""

    field_value = field_value.lower()

    # Convert search fields to their abbreviated forms (e.g. "[title] -> "[ti]")
    field_value = map_to_standard(field_value)

    # Convert search fields to default field constants
    for key, value in SYNTAX_GENERIC_MAP.items():
        if field_value == key:
            return deepcopy(value)

    raise ValueError(f"Field {field_value} not supported by EBSCO")


def generic_search_field_set_to_syntax_set(generic_search_field_set: set) -> set:
    """Convert a set of generic search fields to a set of syntax strings."""

    syntax_set = set()
    for key, value in SYNTAX_GENERIC_MAP.items():
        if generic_search_field_set == value:
            syntax_set.add(key)

    if not syntax_set:
        raise ValueError(
            f"Generic search field set {generic_search_field_set} "
            "not supported by EBSCO"
        )

    return syntax_set
