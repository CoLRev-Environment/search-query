#!/usr/bin/env python3
"""Database and filters."""
from __future__ import annotations

from search_query.database import load_query

FT50 = load_query("journals_FT50")
AIS_8 = load_query("ais_senior_scholars_basket")
AIS_11 = load_query("ais_senior_scholars_list_of_premier_journals")

__all__ = ["FT50", "AIS_8", "AIS_11"]
