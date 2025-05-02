#!/usr/bin/env python3
"""SearchFile parser."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

# pylint: disable=too-few-public-methods


class SearchFile:
    """SearchFile class."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        search_string: str,
        platform: str,
        authors: Optional[list[dict]] = None,
        record_info: Optional[dict] = None,
        date: Optional[dict] = None,
        filepath: Optional[str | Path] = None,
        **kwargs: dict,
    ) -> None:
        self.search_string = search_string
        self.platform = platform
        self.authors = authors or []
        self.record_info = record_info or {}
        self.date = date or {}
        # Note: this will be called search_field_general
        self.search_field = ""
        self._filepath = Path(filepath) if filepath else None

        for key, value in kwargs.items():
            setattr(self, key, value)

        self._validate_authors(self.to_dict())

    def save(self, filepath: Optional[str | Path] = None) -> None:
        """Save the search file to a JSON file."""
        path = Path(filepath) if filepath else self._filepath
        if path is None:
            raise ValueError("No filepath provided and no previous filepath stored.")
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


def load_search_file(filepath: str | Path) -> SearchFile:
    """Load a search file from a JSON file."""
    path = Path(filepath)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if "search_string" not in data or "platform" not in data:
        raise ValueError("File must contain at least 'search_string' and 'platform'.")

    return SearchFile(
        search_string=data.pop("search_string"),
        platform=data.pop("platform"),
        filepath=path,
        **data,
    )
