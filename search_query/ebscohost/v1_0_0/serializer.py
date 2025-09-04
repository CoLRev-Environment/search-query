#!/usr/bin/env python3
"""EBSCO serializer for version 1.0.0."""
from __future__ import annotations

from search_query.ebsco.serializer import EBSCOQuerySerializer

# pylint: disable=too-few-public-methods


class EBCOSerializer_v1_0_0(EBSCOQuerySerializer):
    """EBSCO serializer for version 1.0.0."""

    VERSION = "1.0.0"
