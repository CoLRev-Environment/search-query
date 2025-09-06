#!/usr/bin/env python3
"""Constants for PubMed."""
from __future__ import annotations

import re
import typing
from copy import deepcopy

from search_query.constants import Fields

# fields from https://pubmed.ncbi.nlm.nih.gov/help/
# Note : abstract [ab] is not supported by PubMed

# pylint: disable=too-few-public-methods

SYNTAX_GENERIC_MAP = {
    "[tiab]": {Fields.TITLE, Fields.ABSTRACT},
    "[all]": {Fields.ALL},
    "[ti]": {Fields.TITLE},
    "[au]": {Fields.AUTHOR_KEYWORDS},
    "[sb]": {Fields.FILTER},
    "[ta]": {Fields.JOURNAL},
    "[mh]": {Fields.MESH_TERM},
    "[pt]": {Fields.PUBLICATION_TYPE},
    "[tw]": {Fields.TEXT_WORD},
    "[ad]": {Fields.AFFILIATION},
    "[la]": {Fields.LANGUAGE},
    "[dp]": {Fields.YEAR_PUBLICATION},
}

YEAR_PUBLISHED_FIELD_REGEX: re.Pattern = re.compile(
    r"\[dp\]|\[publication date\]|\[pdat\]", re.IGNORECASE
)

_RAW_PREPROCESSING_MAP: typing.Dict[str, typing.Union[str, typing.Pattern[str]]] = {
    "[ad]": r"\[ad\]|\[affiliation\]",
    "[all]": r"\[all\]|\[all fields\]",
    "[aid]": r"\[aid\]|\[article identifier\]",
    "[au]": r"\[au\]|\[author\]",
    "[auid]": r"\[auid\]|\[author identifier\]",
    "[dcom]": r"\[dcom\]|\[completion date\]",
    "[cois]": r"\[cois\]|\[conflict of interest statement\]",
    "[cn]": r"\[cn\]|\[corporate author\]",
    "[crdt]": r"\[crdt\]|\[create date\]|\[date - create\]",
    "[rn]": r"\[rn\]|\[ec/rn number\]",
    "[ed]": r"\[ed\]|\[editor\]",
    "[edat]": r"\[edat\]|\[entry date\]",
    "[sb]": r"\[sb\]|\[filter\]|\[subset\]",
    "[1au]": r"\[1au\]|\[first author name\]",
    "[fau]": r"\[fau\]|\[full author name\]",
    "[fir]": r"\[fir\]|\[full investigator name\]",
    "[gr]": r"\[gr\]|\[grants and funding\]",
    "[ir]": r"\[ir\]|\[investigator\]",
    "[isbn]": r"\[isbn\]",
    "[ip]": r"\[ip\]|\[issue\]",
    "[ta]": r"\[ta\]|\[journal\]",
    "[la]": r"\[la\]|\[language\]",
    "[lastau]": r"\[lastau\]|\[last author name\]",
    "[lid]": r"\[lid\]|\[location id\]",
    "[mhda]": r"\[mhda\]|\[mesh date\]",
    "[mh]": (
        r"\[mh\]|\[mesh\]|\[mesh terms\]|\[mesh terms:noexp\]|"
        r"\[mh:noexp\]|\[mesh:noexp\]|\[mesh major topic\]|"
        r"\[majr\]|\[mj\]|\[mesh subheading\]|\[subheading\]|\[sh\]"
    ),
    "[lr]": r"\[lr\]|\[modification date\]",
    "[jid]": r"\[jid\]|\[nlm unique id\]",
    "[ot]": r"\[ot\]|\[other term\]",
    "[pg]": r"\[pg\]|\[pagination\]",
    "[ps]": r"\[ps\]|\[personal name as subject\]",
    "[pa]": r"\[pa\]|\[pharmacological action\]",
    "[pl]": r"\[pl\]|\[place of publication\]",
    "[dp]": YEAR_PUBLISHED_FIELD_REGEX,
    "[pt]": r"\[pt\]|\[publication type\]",
    "[pubn]": r"\[pubn\]|\[publisher\]",
    "[si]": r"\[si\]|\[secondary source id\]",
    "[nm]": r"\[nm\]|\[supplementary concept\]",
    "[tw]": r"\[tw\]|\[text word\]",
    "[ti]": r"\[ti\]|\[title\]",
    "[tiab]": r"\[tiab\]|\[title/abstract\]",
    "[tt]": r"\[tt\]|\[transliterated title\]",
    "[vi]": r"\[vi\]|\[volume\]",
}

PREPROCESSING_MAP = {
    k: re.compile(v, re.IGNORECASE) if isinstance(v, str) else v
    for k, v in _RAW_PREPROCESSING_MAP.items()
}

PROXIMITY_SEARCH_REGEX = re.compile(
    r"^\[(ti|tiab|ad|title|title\/abstract|affiliation):\~([0-9]+)\]$",
    flags=re.IGNORECASE,
)

_VF_ELEMENTS = [
    v.pattern for v in list(PREPROCESSING_MAP.values()) + [PROXIMITY_SEARCH_REGEX]
]
VALID_fieldS_REGEX = re.compile(
    "|".join(_VF_ELEMENTS), flags=re.IGNORECASE  # type: ignore
)


def map_to_standard(syntax_str: str) -> str:
    """Map a syntax string to a standard syntax string."""
    syntax_str = syntax_str.lower()
    syntax_str = syntax_str.strip(" []")
    syntax_str = f"[{syntax_str}]"

    for standard_key, variation_regex in PREPROCESSING_MAP.items():
        if variation_regex.match(syntax_str):
            return standard_key
    raise ValueError


def syntax_str_to_generic_field_set(field_value: str) -> set:
    """Translate a search field"""

    field_value = field_value.lower()
    field_value = field_value.strip(" []")
    field_value = f"[{field_value}]"

    # Convert search fields to their abbreviated forms (e.g. "[title] -> "[ti]")
    field_value = map_to_standard(field_value)

    # Convert search fields to default field constants
    for key, value in SYNTAX_GENERIC_MAP.items():
        if field_value == key:
            return deepcopy(value)

    raise ValueError(f"Field {field_value} not supported by PubMed")  # pragma: no cover


def generic_field_to_syntax_field(generic_field: str) -> str:
    """Convert a set of generic search fields to a set of syntax strings."""

    for key, value in SYNTAX_GENERIC_MAP.items():
        if {generic_field} == value:
            return key

    for key, value in SYNTAX_GENERIC_MAP.items():
        if {generic_field} & value:
            return key

    raise ValueError(  # pragma: no cover
        f"Generic search field set {generic_field} " "not supported by Pubmed"
    )
