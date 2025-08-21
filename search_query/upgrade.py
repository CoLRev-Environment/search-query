#!/usr/bin/env python3
"""Upgrade a SearchQuery."""
from typing import Optional
from search_query.parser import PARSERS, LATEST_VERSIONS
from search_query.translators import TRANSLATORS # TODO : create this file
from search_query.serializers import SERIALIZERS # TODO: create this file

# generic, non–platform-specific upgrade method

def upgrade_query(
    query_str: str,
    platform: str,
    version_current: str,
    version_target: Optional[str],
) -> str:
    """
    Upgrade a database-specific search query from one syntax *version* to another
    using the generic query as a platform-agnostic intermediate representation (IR).

    Design intent:
    - Parse specific query → generic query (IR) → specific query → serialize. 
      By pivoting through a generic IR we avoid
      O(N^2) pairwise converters, improving maintainability and testability.
    - Each platform/version only needs: PARSER, TRANSLATOR (to/from IR), SERIALIZER.
      Adding a new version/platform becomes linear work (plug-in modules).
    - Unsupported features can be flagged with warnings instead of failing silently.
    - Using the same `to_generic_syntax()` / `to_specific_syntax()` for upgrades
      and cross-platform translations ensures consistency and reduces effort.
    - A round-trip parse after serialization confirms syntactic validity.

    Notes:
    - The IR should be the most expressive model across supported syntaxes.
      Where unavoidable, translators should emit warnings about lossy conversions.
    """

    if not version_target:
        version_target = LATEST_VERSIONS[platform]  # e.g., {"pubmed": "v3", ...}

    # 1) Parse source query string into a query object.
    parser_cls = PARSERS[platform][version_current]
    source_ast = parser_cls.parse(query_str)

    # 2) Translate platform/version-specific query → generic query (IR).
    translator_cls_current = TRANSLATORS[platform][version_current]
    generic_ir = translator_cls_current.to_generic_syntax(source_ast)

    # 3) Translate generic query (IR) → target platform/version query.
    translator_cls_target = TRANSLATORS[platform][version_target]
    target_ast = translator_cls_target.to_specific_syntax(generic_ir)

    # 4) Serialize target query → query string.
    serializer_cls = SERIALIZERS[platform][version_target]
    upgraded_query_str = serializer_cls.to_string(target_ast)

    # 5) Safety check: re-parse in the target version to validate output.
    parser_cls_target = PARSERS[platform][version_target]
    _ = parser_cls_target.parse(upgraded_query_str)

    return upgraded_query_str