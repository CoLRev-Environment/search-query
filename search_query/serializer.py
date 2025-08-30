"""Version-aware serializer dispatch."""

from search_query.pubmed.v1_0_0.serializer import PubMedSerializer_v1_0_0
from search_query.wos.v1_0_0.serializer import WOSSerializer_v1_0_0
from search_query.ebsco.v1_0_0.serializer import EBCOSerializer_v1_0_0


SERIALIZERS: dict[str, dict[str, object]] = {
    "pubmed": {"1.0.0": PubMedSerializer_v1_0_0},
    "wos": {"1.0.0": WOSSerializer_v1_0_0},
    "ebsco": {"1.0.0": EBCOSerializer_v1_0_0},
}


LATEST_SERIALIZER_VERSIONS = {k: max(v.keys()) for k, v in SERIALIZERS.items()}


__all__ = ["SERIALIZERS", "LATEST_SERIALIZER_VERSIONS"]

