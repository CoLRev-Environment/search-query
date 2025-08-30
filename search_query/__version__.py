# pylint: disable=missing-module-docstring
try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:  # pragma: no cover
    from importlib_metadata import PackageNotFoundError, version  # type: ignore

try:  # pragma: no cover - fallback if package metadata is missing
    __version__ = version("search_query")
except PackageNotFoundError:
    __version__ = "0.0.0"
