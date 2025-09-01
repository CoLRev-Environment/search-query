#!/usr/bin/env python3
"""Version-aware translator dispatch."""
from __future__ import annotations

import typing

from packaging.version import Version

from search_query.ebsco.v1_0_0.translator import EBSCOTranslator_v1_0_0
from search_query.pubmed.v1_0_0.translator import PubMedTranslator_v1_0_0
from search_query.translator_base import QueryTranslator
from search_query.wos.v1_0_0.translator import WOSTranslator_v1_0_0

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import Type

TRANSLATORS: Dict[str, Dict[str, Type[QueryTranslator]]] = {
    "pubmed": {"1.0.0": PubMedTranslator_v1_0_0},
    "wos": {"1.0.0": WOSTranslator_v1_0_0},
    "ebscohost": {"1.0.0": EBSCOTranslator_v1_0_0},
}


LATEST_TRANSLATOR_VERSIONS = {k: max(v.keys()) for k, v in TRANSLATORS.items()}

LATEST_TRANSLATORS = {k: v[max(v.keys(), key=Version)] for k, v in TRANSLATORS.items()}
