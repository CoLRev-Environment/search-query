# pylint: disable=missing-module-docstring
"""Project version information."""

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:  # pragma: no cover
    # For Python < 3.8
    from importlib_metadata import PackageNotFoundError, version  # type: ignore

try:
    __version__ = version("search_query")
except PackageNotFoundError:  # pragma: no cover - when package isn't installed
    __version__ = "0+unknown"
