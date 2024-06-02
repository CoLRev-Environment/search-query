#!/usr/bin/env python
"""Constants for search-query"""
# pylint: disable=too-few-public-methods


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
    NEAR = "NEAR"


class Colors:
    """Colors for CLI printing"""

    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"
