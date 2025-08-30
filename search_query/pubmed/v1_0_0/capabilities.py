"""Capabilities of the PubMed 1.0.0 syntax."""

FEATURES = {
    "proximity": False,
    "phrase_quotes": True,
    "field_aliases": {"Title/Abstract": ["Title", "Abstract", "TIAB"]},
    "max_query_len": None,
}

