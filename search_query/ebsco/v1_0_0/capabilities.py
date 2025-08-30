"""Capabilities for EBSCO 1.0.0."""

FEATURES = {
    "proximity": True,
    "phrase_quotes": True,
    "field_aliases": {"Title/Abstract": ["TI", "AB"]},
    "max_query_len": None,
}

