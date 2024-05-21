#!/usr/bin/env python
"""Constants for search-query"""
# pylint: disable=too-few-public-methods
import typing
from enum import Enum
from pathlib import Path


class Fields:
    """Search fields"""
    AUTHOR_KEYWORDS = "Author Keywords"
    ABSTRACT = "Abstract"
    AUTHOR = "Author"
    DOI = "DOI"
    ISBN_ISSN = "ISBN/ISSN"
    PUBLISHER = "Publisher"
    TITLE = "Title"

class Operators: 
    """Operators"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"