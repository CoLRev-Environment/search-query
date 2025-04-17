"""Top-level package for SearchQuery."""

__author__ = """Gerit Wagner"""
__email__ = "gerit.wagner@hec.ca"

from search_query.query import Query
from search_query.query_or import OrQuery
from search_query.query_and import AndQuery
from search_query.query_near import NEARQuery
from .__version__ import __version__

__all__ = ["__version__", "Query", "OrQuery", "AndQuery", "NEARQuery"]

# Instead of adding elements to __all__,
# prefixing methods/variables with "__" is preferred.
# Imports like "from x import *" are discouraged.
