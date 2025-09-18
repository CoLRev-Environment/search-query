#!/usr/bin/env python3
"""SearchFile parser."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional
from typing import Union

# pylint: disable=too-few-public-methods

_HISTORY_SUFFIX = "_search_history.json"


# pylint: disable=too-many-instance-attributes
class SearchFile:
    """SearchFile class."""

    _search_history_path: Optional[Path] = None

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        search_string: str,
        platform: str,
        authors: Optional[list[dict]] = None,
        record_info: Optional[dict] = None,
        date: Optional[dict] = None,
        search_results_path: Optional[str | Path] = None,
        **kwargs: dict,
    ) -> None:
        self.search_string = search_string
        self.platform = platform
        self.authors = authors or []
        self.record_info = record_info or {}
        self.date = date or {}
        # Note: this will be called field_general
        self.field = ""
        self.set_search_results_path(search_results_path)

        for key, value in kwargs.items():
            setattr(self, key, value)

        self._validate_authors(self.to_dict())

    def set_search_results_path(self, path: Optional[Union[str, Path]]) -> None:
        """
        Set or clear the explicit search-results file path.
        Passing None clears the path.
        """
        if path is None:
            self.search_results_path = None
            return

        self.search_results_path = Path(path)
        if self.search_results_path.name.endswith(_HISTORY_SUFFIX):
            raise ValueError(
                f"search_results_path must not end with '{_HISTORY_SUFFIX}'."
            )

    def set_search_history_file_path(self, path: Optional[Union[str, Path]]) -> None:
        """
        Set or clear the explicit search-history file path (stored privately).
        Passing None clears the override so the derived path is used again.
        """
        if path is None:
            self._search_history_path = None
            return

        self._search_history_path = Path(path)

    def get_search_history_path(
        self, search_history_path: Optional[str | Path] = None
    ) -> Path:
        """Get the search history path."""

        if search_history_path:
            return Path(search_history_path)

        if self._search_history_path is not None:
            return self._search_history_path

        if getattr(self, "search_results_path", None) is None:
            raise ValueError(
                "No search_history_path provided and no search_results_path stored."
            )

        rp = Path(self.search_results_path)  # type: ignore
        return rp.with_name(rp.stem + _HISTORY_SUFFIX)

    def save(self, search_history_path: Optional[str | Path] = None) -> None:
        """Save the search file to a JSON file."""
        path = self.get_search_history_path(search_history_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)

    def to_dict(self) -> dict:
        """Convert the search file to a dictionary."""
        data = {
            "search_string": self.search_string,
            "platform": self.platform,
            "authors": self.authors,
            "record_info": self.record_info,
            "date": self.date,
        }
        if self.search_results_path is not None:
            data["search_results_path"] = str(self.search_results_path)
        extras = {
            k: v
            for k, v in self.__dict__.items()
            if k not in data and not k.startswith("_") and v is not None
        }
        data.update(extras)
        return data

    def _validate_authors(self, data: dict) -> None:
        if "authors" not in data:
            raise ValueError("Data must have an 'authors' key.")
        if not isinstance(data["authors"], list):
            raise TypeError("Authors must be a list.")
        for author in data["authors"]:
            if not isinstance(author, dict):
                raise TypeError("Author must be a dictionary.")
            if "name" not in author:
                raise ValueError("Author must have a 'name' key.")
            if not isinstance(author["name"], str):
                raise TypeError("Author name must be a string.")

            if "ORCID" in author:
                if not isinstance(author["ORCID"], str):
                    raise TypeError("ORCID must be a string.")
                if not re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$", author["ORCID"]):
                    raise ValueError("Invalid ORCID.")

            if "email" in author:
                if not isinstance(author["email"], str):
                    raise TypeError("Email must be a string.")
                if not re.match(r"^\S+@\S+\.\S+$", author["email"]):
                    raise ValueError("Invalid email.")


def load_search_file(search_history_path: str | Path) -> SearchFile:
    """Load a search file from a JSON file."""
    path = Path(search_history_path)
    if not path.exists():
        raise FileNotFoundError(f"File {path} does not exist.")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if "search_string" not in data or "platform" not in data:
        raise ValueError("File must contain at least 'search_string' and 'platform'.")

    search_file = SearchFile(
        search_string=data.pop("search_string"),
        platform=data.pop("platform"),
        **data,
    )
    search_file.set_search_history_file_path(path)
    return search_file
