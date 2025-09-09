# pylint: disable=missing-module-docstring
try:
    from importlib.metadata import version
except ImportError:  # pragma: no cover
    # For Python < 3.8
    from importlib_metadata import version  # type: ignore

try:
    __version__ = version("search_query")
except Exception:  # pragma: no cover - fallback when package metadata missing
    __version__ = "0.0.0"
