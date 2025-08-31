#!/usr/bin/env python3
"""PubMed serializer for version 1.0.0."""
from __future__ import annotations

from search_query.pubmed.serializer import PUBMEDQuerySerializer


# pylint: disable=too-few-public-methods


class PubMedSerializer_v1_0_0(PUBMEDQuerySerializer):
    """PubMed serializer for version 1.0.0."""

    VERSION = "1.0.0"
