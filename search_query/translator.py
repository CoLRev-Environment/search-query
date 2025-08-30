"""Version-aware translator dispatch."""

from search_query.pubmed.v1_0_0.translator import PubMedTranslator_v1_0_0
from search_query.wos.v1_0_0.translator import WOSTranslator_v1_0_0
from search_query.ebsco.v1_0_0.translator import EBCOTranslator_v1_0_0


TRANSLATORS: dict[str, dict[str, object]] = {
    "pubmed": {"1.0.0": PubMedTranslator_v1_0_0},
    "wos": {"1.0.0": WOSTranslator_v1_0_0},
    "ebsco": {"1.0.0": EBCOTranslator_v1_0_0},
}


LATEST_TRANSLATOR_VERSIONS = {k: max(v.keys()) for k, v in TRANSLATORS.items()}


__all__ = ["TRANSLATORS", "LATEST_TRANSLATOR_VERSIONS"]

