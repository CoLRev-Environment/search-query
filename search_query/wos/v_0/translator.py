#!/usr/bin/env python3
"""Web of Science translator for version 0."""
from __future__ import annotations

import typing
import warnings

from search_query.constants import Fields
from search_query.query import Query
from search_query.wos.translator import WOSTranslator

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.registry import Registry


class WOSTranslator_v0(WOSTranslator):
    """Translator for WOS queries."""

    VERSION = "0"

    #: Mapping of deprecated field tags used by WOS ``0`` to
    #: generic search fields.  Only a subset of tags are supported; tags
    #: without a mapping will trigger a warning and the corresponding
    #: term will be dropped during translation.
    DEPRECATED_FIELD_MAP = {
        "AF=": Fields.AUTHOR,
        "BA=": Fields.AUTHOR,
        "BF=": Fields.GROUP_AUTHOR,
        "BE=": Fields.EDITOR,
        "C1=": Fields.ADDRESS,
        "RP=": Fields.ADDRESS,
        "DE=": Fields.AUTHOR_KEYWORDS,
        "ID=": Fields.KEYWORDS_PLUS,
        "DI=": Fields.DOI,
        "RI=": Fields.AUTHOR_IDENTIFIERS,
        "OI=": Fields.AUTHOR_IDENTIFIERS,
        "SN=": Fields.ISSN_ISBN,
        "EI=": Fields.ISSN_ISBN,
        "BN=": Fields.ISSN_ISBN,
    }

    @classmethod
    def translate_fields_to_generic(cls, query: Query) -> None:
        """Translate deprecated 0 field tags to generic field names."""

        if query.field:
            field_val = query.field.value

            if field_val in cls.DEPRECATED_FIELD_MAP:
                query.field.value = cls.DEPRECATED_FIELD_MAP[field_val]
            else:
                # Try default translation first; if it fails, emit a warning
                # and drop the term as it cannot be represented in newer
                # versions.
                try:
                    super().translate_fields_to_generic(query)
                except ValueError:
                    warnings.warn(
                        f"Field '{field_val}' is deprecated and cannot be "
                        "translated; the term will be ignored.",
                        UserWarning,
                        stacklevel=2,
                    )
                    parent = query.get_parent()
                    if parent:
                        parent.children.remove(query)

            return

        for child in list(query.children):
            cls.translate_fields_to_generic(child)


def register(registry: Registry, *, platform: str, version: str) -> None:
    """Register this translator with the ``registry``."""

    registry.register_translator(platform, version, WOSTranslator_v0)
