"""Compatibility matrix for parser/serializer/translator versions."""

from __future__ import annotations

from search_query.parser import PARSERS
from search_query.serializer import SERIALIZERS
from search_query.translator import TRANSLATORS


def _build_matrix() -> dict:
    matrix: dict[str, dict[str, dict[str, list[str] | list]]] = {}
    for platform, versions in PARSERS.items():
        matrix[platform] = {}
        for version in versions:
            matrix[platform][version] = {
                "serializer": list(SERIALIZERS.get(platform, {}).keys()),
                "translator": list(TRANSLATORS.get(platform, {}).keys()),
                "notes": [],
            }
    return matrix


COMPAT_MATRIX = _build_matrix()


def assert_compatible(
    platform: str, parser_v: str, serializer_v: str, translator_v: str
) -> None:
    """Ensure that the requested versions are compatible."""

    compat = COMPAT_MATRIX.get(platform, {}).get(parser_v)
    if not compat:
        raise ValueError("unknown parser version")
    if serializer_v not in compat["serializer"]:
        raise ValueError("incompatible serializer version")
    if translator_v not in compat["translator"]:
        raise ValueError("incompatible translator version")


__all__ = ["COMPAT_MATRIX", "assert_compatible"]

