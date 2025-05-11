#!/usr/bin/env python3
"""Constants for PubMed."""
# pylint: disable=too-few-public-methods
import re
from copy import deepcopy

from search_query.constants import Fields

# fields from https://pubmed.ncbi.nlm.nih.gov/help/
# Note : abstract [ab] is not supported by PubMed

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
    "[dp]": {Fields.PUBLICATION_DATE},
}

_RAW_PREPROCESSING_MAP = {
    "[ad]": r"\[ad\]|\[affiliation\]",
    "[all]": r"\[all\]|\[all fields\]",
    "[aid]": r"\[aid\]|\[article identifier\]",
    "[au]": r"\[au\]|\[author\]",
    "[auid]": r"\[auid\]|\[author identifier\]",
    "[dcom]": r"\[dcom\]|\[completion date\]",
    "[cois]": r"\[cois\]|\[conflict of interest statement\]",
    "[cn]": r"\[cn\]|\[corporate author\]",
    "[crdt]": r"\[crdt\]|\[create date\]",
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
    "[dp]": r"\[dp\]|\[publication date\]|\[pdate\]",
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
VALID_FIELDS_REGEX = re.compile(
    "|".join(_VF_ELEMENTS), flags=re.IGNORECASE  # type: ignore
)


def map_to_standard(syntax_str: str) -> str:
    """Map a syntax string to a standard syntax string."""
    for standard_key, variation_regex in PREPROCESSING_MAP.items():
        if variation_regex.match(syntax_str):
            return standard_key
    raise ValueError


def syntax_str_to_generic_search_field_set(field_value: str) -> set:
    """Translate a search field"""

    field_value = field_value.lower()

    # Convert search fields to their abbreviated forms (e.g. "[title] -> "[ti]")
    field_value = map_to_standard(field_value)

    # Convert search fields to default field constants
    for key, value in SYNTAX_GENERIC_MAP.items():
        if field_value == key:
            return deepcopy(value)

    raise ValueError(f"Field {field_value} not supported by PubMed")


def generic_search_field_set_to_syntax_set(generic_search_field_set: set) -> set:
    """Convert a set of generic search fields to a set of syntax strings."""

    syntax_set = set()

    # for generic_search_field in generic_search_field_set:
    for key, value in SYNTAX_GENERIC_MAP.items():
        if generic_search_field_set == value:
            syntax_set.add(key)
            # will add [tiab] for {ti, ab} but not [ti]

    if not syntax_set:
        raise ValueError(
            f"Generic search field set {generic_search_field_set} "
            "not supported by PubMed"
        )

    return syntax_set
