#!/usr/bin/env python3
"""Version-aware serializer dispatch."""
from __future__ import annotations

import typing

from packaging.version import Version

from search_query.ebsco.v1_0_0.serializer import EBCOSerializer_v1_0_0
from search_query.generic.serializer import GenericSerializer
from search_query.pubmed.v1_0_0.serializer import PubMedSerializer_v1_0_0
from search_query.serializer_base import StringSerializer
from search_query.wos.v1_0_0.serializer import WOSSerializer_v1_0_0

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import Type

SERIALIZERS: Dict[str, Dict[str, Type[StringSerializer]]] = {
    "pubmed": {"1.0.0": PubMedSerializer_v1_0_0},
    "wos": {"1.0.0": WOSSerializer_v1_0_0},
    "ebscohost": {"1.0.0": EBCOSerializer_v1_0_0},
    "generic": {"1.0.0": GenericSerializer},
}


LATEST_SERIALIZERS = {k: v[max(v.keys(), key=Version)] for k, v in SERIALIZERS.items()}
