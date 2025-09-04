#!/usr/bin/env python3
"""Registry for search query components."""
from __future__ import annotations

import importlib
import re
import typing as _t
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

if _t.TYPE_CHECKING:  # pragma: no cover
    from typing import Dict
    from typing import Type

from packaging.version import Version

from search_query.constants import PLATFORM
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.serializer_base import StringSerializer as QueryListSerializer
from search_query.serializer_base import StringSerializer as QueryStringSerializer
from search_query.translator_base import QueryTranslator

_VERSION_DIR_RE = re.compile(r"^v_(\d+)_(\d+)_(\d+)$")
_MODULE_FILES = ("parser", "serializer", "translator")


def _to_version_str(dir_name: str) -> str:
    m = _VERSION_DIR_RE.match(dir_name)
    if not m:
        raise ValueError(f"Invalid version directory name: {dir_name!r}")
    return ".".join(m.groups())


def _platform_pkg_path(platform: str) -> Path:
    pkg = f"search_query.{platform}"
    mod = importlib.import_module(pkg)
    return Path(next(iter(getattr(mod, "__path__"))))


@dataclass
class _Registry:
    # Parsers
    parsers: Dict[str, Dict[str, Type[QueryStringParser]]] = field(default_factory=dict)
    list_parsers: Dict[str, Dict[str, Type[QueryListParser]]] = field(
        default_factory=dict
    )
    # Serializers
    serializers: Dict[str, Dict[str, Type[QueryStringSerializer]]] = field(
        default_factory=dict
    )
    list_serializers: Dict[str, Dict[str, Type[QueryListSerializer]]] = field(
        default_factory=dict
    )
    # Translators
    translators: Dict[str, Dict[str, Type[QueryTranslator]]] = field(
        default_factory=dict
    )

    # --- register methods (fail on duplicates) ---
    def register_parser_string(
        self, platform: str, version: str, cls: Type[QueryStringParser]
    ) -> None:
        self.parsers.setdefault(platform, {})
        if version in self.parsers[platform]:
            prev = self.parsers[platform][version]
            raise RuntimeError(
                f"Duplicate string parser for {platform} {version}: {prev.__name__} vs {cls.__name__}"
            )
        self.parsers[platform][version] = cls  # type: ignore[assignment]

    def register_parser_list(
        self, platform: str, version: str, cls: Type[QueryListParser]
    ) -> None:
        self.list_parsers.setdefault(platform, {})
        if version in self.list_parsers[platform]:
            prev = self.list_parsers[platform][version]
            raise RuntimeError(
                f"Duplicate list parser for {platform} {version}: {prev.__name__} vs {cls.__name__}"
            )
        self.list_parsers[platform][version] = cls  # type: ignore[assignment]

    def register_serializer_string(
        self, platform: str, version: str, cls: Type[QueryStringSerializer]
    ) -> None:
        self.serializers.setdefault(platform, {})
        if version in self.serializers[platform]:
            prev = self.serializers[platform][version]
            raise RuntimeError(
                f"Duplicate string serializer for {platform} {version}: {prev.__name__} vs {cls.__name__}"
            )
        self.serializers[platform][version] = cls  # type: ignore[assignment]

    def register_serializer_list(
        self, platform: str, version: str, cls: Type[QueryListSerializer]
    ) -> None:
        self.list_serializers.setdefault(platform, {})
        if version in self.list_serializers[platform]:
            prev = self.list_serializers[platform][version]
            raise RuntimeError(
                f"Duplicate list serializer for {platform} {version}: {prev.__name__} vs {cls.__name__}"
            )
        self.list_serializers[platform][version] = cls  # type: ignore[assignment]

    def register_translator(
        self, platform: str, version: str, cls: Type[QueryTranslator]
    ) -> None:
        self.translators.setdefault(platform, {})
        if version in self.translators[platform]:
            prev = self.translators[platform][version]
            raise RuntimeError(
                f"Duplicate translator for {platform} {version}: {prev.__name__} vs {cls.__name__}"
            )
        self.translators[platform][version] = cls  # type: ignore[assignment]


# Public registries ------------------------------------------------------------

PARSERS: dict[str, dict[str, type[QueryStringParser]]] = {}
LIST_PARSERS: dict[str, dict[str, type[QueryListParser]]] = {}

SERIALIZERS: dict[str, dict[str, type[QueryStringSerializer]]] = {}
LIST_SERIALIZERS: dict[str, dict[str, type[QueryListSerializer]]] = {}

TRANSLATORS: dict[str, dict[str, type[QueryTranslator]]] = {}

# Discovery -------------------------------------------------------------------

_reg = _Registry(
    parsers=PARSERS,
    list_parsers=LIST_PARSERS,
    serializers=SERIALIZERS,
    list_serializers=LIST_SERIALIZERS,
    translators=TRANSLATORS,
)

for plat in PLATFORM:
    plat_key = plat.value
    # ensure keys exist
    PARSERS.setdefault(plat_key, {})
    LIST_PARSERS.setdefault(plat_key, {})
    SERIALIZERS.setdefault(plat_key, {})
    LIST_SERIALIZERS.setdefault(plat_key, {})
    TRANSLATORS.setdefault(plat_key, {})

    pkg_path = _platform_pkg_path(plat_key)
    for child in pkg_path.iterdir():
        if not child.is_dir():
            continue
        if not _VERSION_DIR_RE.match(child.name):
            continue
        version_str = _to_version_str(child.name)

        for modstub in _MODULE_FILES:
            pyfile = child / f"{modstub}.py"
            if not pyfile.is_file():
                continue
            mod_name = f"search_query.{plat_key}.{child.name}.{modstub}"
            mod = importlib.import_module(mod_name)

            register = getattr(mod, "register", None)
            if register is None or not callable(register):
                raise RuntimeError(
                    f"{mod_name} must define a callable register(registry, *, platform: str, version: str)"
                )

            register(_reg, platform=plat_key, version=version_str)

# Sanity checks ---------------------------------------------------------------


def _check_pair(
    name_a: str,
    m_a: dict[str, dict[str, object]],
    name_b: str,
    m_b: dict[str, dict[str, object]],
    platform: str,
) -> None:
    if set(m_a[platform].keys()) != set(m_b[platform].keys()):
        raise RuntimeError(
            f"Mismatched versions for platform '{platform}' between {name_a} and {name_b}: "
            f"{sorted(m_a[platform].keys())} vs {sorted(m_b[platform].keys())}"
        )


for plat in PLATFORM:
    # Only check if any entries exist
    if PARSERS[plat.value] or LIST_PARSERS[plat.value]:
        _check_pair("PARSERS", PARSERS, "LIST_PARSERS", LIST_PARSERS, plat.value)
    if SERIALIZERS[plat.value] or LIST_SERIALIZERS[plat.value]:
        _check_pair(
            "SERIALIZERS", SERIALIZERS, "LIST_SERIALIZERS", LIST_SERIALIZERS, plat.value
        )

# Latest helpers --------------------------------------------------------------


def _latest_map(m: dict[str, dict[str, object]]) -> dict[str, str]:
    return {k: max(v.keys(), key=Version) for k, v in m.items() if v}


LATEST_VERSIONS_PARSERS: dict[str, str] = _latest_map(PARSERS)
LATEST_PARSERS: dict[str, type[QueryStringParser]] = {
    k: PARSERS[k][LATEST_VERSIONS_PARSERS[k]] for k in LATEST_VERSIONS_PARSERS
}
LATEST_LIST_PARSERS: dict[str, type[QueryListParser]] = {
    k: LIST_PARSERS[k][LATEST_VERSIONS_PARSERS[k]] for k in LATEST_VERSIONS_PARSERS
}

LATEST_VERSIONS_SERIALIZERS: dict[str, str] = _latest_map(SERIALIZERS)
LATEST_SERIALIZERS: dict[str, type[QueryStringSerializer]] = {
    k: SERIALIZERS[k][LATEST_VERSIONS_SERIALIZERS[k]]
    for k in LATEST_VERSIONS_SERIALIZERS
}
LATEST_LIST_SERIALIZERS: dict[str, type[QueryListSerializer]] = {
    k: LIST_SERIALIZERS[k][LATEST_VERSIONS_SERIALIZERS[k]]
    for k in LATEST_VERSIONS_SERIALIZERS
}

LATEST_VERSIONS_TRANSLATORS: dict[str, str] = _latest_map(TRANSLATORS)
LATEST_TRANSLATORS: dict[str, type[QueryTranslator]] = {
    k: TRANSLATORS[k][LATEST_VERSIONS_TRANSLATORS[k]]
    for k in LATEST_VERSIONS_TRANSLATORS
}
