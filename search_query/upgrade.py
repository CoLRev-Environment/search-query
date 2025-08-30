"""Utilities for upgrading search queries between versions."""

from __future__ import annotations

from typing import Optional

from search_query.parser import LATEST_VERSIONS, PARSERS
from search_query.serializer import SERIALIZERS
from search_query.translator import TRANSLATORS


def upgrade_query(
    query_str: str,
    platform: str,
    version_current: str,
    version_target: Optional[str] = None,
) -> str:
    """Upgrade a database-specific query string to another version."""

    if not version_target or version_target.lower() == "latest":
        version_target = LATEST_VERSIONS[platform]

    # Parse source string
    parser_cls = PARSERS[platform][version_current]
    source_ast = parser_cls(query_str).parse()  # type: ignore[arg-type]

    # Translate to generic IR
    translator_cls_current = TRANSLATORS[platform][version_current]
    generic_ir = translator_cls_current.to_generic_syntax(source_ast)

    # Translate to target specific syntax
    translator_cls_target = TRANSLATORS[platform][version_target]
    target_ast = translator_cls_target.to_specific_syntax(generic_ir)

    # Serialize to string
    serializer_cls = SERIALIZERS[platform][version_target]
    serializer = serializer_cls() if callable(serializer_cls) else serializer_cls
    upgraded_query_str = serializer.to_string(target_ast)  # type: ignore[call-arg]

    # Validate by re-parsing with target parser
    parser_cls_target = PARSERS[platform][version_target]
    parser_cls_target(upgraded_query_str).parse()  # type: ignore[arg-type]

    return upgraded_query_str


__all__ = ["upgrade_query"]

