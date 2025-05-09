#!/usr/bin/env python3
"""Constants for PubMed."""
# pylint: disable=too-few-public-methods
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP

DEFAULT_FIELD_MAP = {
    "[affiliation]": "[ad]",
    "[all fields]": "[all]",
    "[article identifier]": "[aid]",
    "[author]": "[au]",
    "[author identifier]": "[auid]",
    "[completion date]": "[dcom]",
    "[conflict of interest statement]": "[cois]",
    "[corporate author]": "[cn]",
    "[create date]": "[crdt]",
    "[ec/rn number]": "[rn]",
    "[editor]": "[ed]",
    "[entry date]": "[edat]",
    "[filter]": "[sb]",
    "[first author name]": "[1au]",
    "[full author name]": "[fau]",
    "[full investigator name]": "[fir]",
    "[grants and funding]": "[gr]",
    "[investigator]": "[ir]",
    "[isbn]": "[isbn]",
    "[issue]": "[ip]",
    "[journal]": "[ta]",
    "[language]": "[la]",
    "[last author name]": "[lastau]",
    "[location id]": "[lid]",
    "[mesh date]": "[mhda]",
    "[mesh]": "[mh]",
    "[mesh terms]": "[mh]",
    "[mesh terms:noexp]": "[mh]",
    "[mh:noexp]": "[mh]",
    "[mesh:noexp]": "[mh]",
    "[mesh major topic]": "[mh]",
    "[majr]": "[mh]",
    "[mj]": "[mh]",
    "[mesh subheading]": "[mh]",
    "[subheading]": "[mh]",
    "[sh]": "[mh]",
    "[modification date]": "[lr]",
    "[nlm unique id]": "[jid]",
    "[other term]": "[ot]",
    "[pagination]": "[pg]",
    "[personal name as subject]": "[ps]",
    "[pharmacological action]": "[pa]",
    "[place of publication]": "[pl]",
    "[publication date]": "[dp]",
    "[pdate]": "[dp]",
    "[publication type]": "[pt]",
    "[publisher]": "[pubn]",
    "[secondary source id]": "[si]",
    "[subset]": "[sb]",
    "[supplementary concept]": "[nm]",
    "[text word]": "[tw]",
    "[title]": "[ti]",
    "[title/abstract]": "[tiab]",
    "[transliterated title]": "[tt]",
    "[volume]": "[vi]",
}

FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.PUBMED]


def map_search_field(field_value: str) -> str:
    """Translate a search field"""

    field_value = field_value.lower()

    # Convert search fields to their abbreviated forms (e.g. "[title] -> "[ti]")
    field_value = DEFAULT_FIELD_MAP.get(field_value, field_value)
    # Convert search fields to default field constants
    field_value = FIELD_TRANSLATION_MAP.get(field_value, field_value)

    return field_value
