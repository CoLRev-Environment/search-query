"""Top-level package for SearchQuery."""

__author__ = """Gerit Wagner"""
__email__ = "gerit.wagner@hec.ca"

from search_query.or_query import OrQuery
from search_query.and_query import AndQuery
from .__version__ import __version__

__all__ = ["__version__", "OrQuery", "AndQuery"]

# Instead of adding elements to __all__,
# prefixing methods/variables with "__" is preferred.
# Imports like "from x import *" are discouraged.
