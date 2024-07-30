#!/usr/bin/env python3
"""SearchFile parser."""
from __future__ import annotations

import json
import re
import typing

# pylint: disable=too-few-public-methods


class SearchFile:
    """SearchFile model."""

    record_info: typing.Dict[str, str]
    authors: typing.List[dict]
    date: dict
    platform: str
    database: typing.List[str]
    search_string: str

    # Optionals
    parsed: typing.Optional[dict] = None
    string_name: typing.Optional[str] = None
    keywords: typing.Optional[str] = None
    related_records: typing.Optional[str] = None
    parent_record: typing.Optional[str] = None
    database_time_coverage: typing.Optional[str] = None
    search_language: typing.Optional[str] = None
    settings: typing.Optional[str] = None
    quality_assurance: typing.Optional[str] = None
    validation_report: typing.Optional[str] = None
    peer_review: typing.Optional[str] = None
    description: typing.Optional[str] = None
    review_question: typing.Optional[str] = None
    review_type: typing.Optional[str] = None
    linked_protocol: typing.Optional[str] = None
    linked_report: typing.Optional[str] = None

    def __init__(self, filepath: str) -> None:
        with open(filepath, encoding="utf-8") as file:
            data = json.load(file)

        self._validate(data)

        self.record_info = data["record_info"]
        self.authors = data["authors"]
        self.date = data["date"]
        self.platform = data["platform"]
        self.database = data["database"]
        self.search_string = data["search_string"]
        if "parsed" in data:
            self.parsed = data["parsed"]

    def _validate(self, data: dict) -> None:
        # Note: validate without pydantic to keep zero dependencies

        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary.")

        self._validate_authors(data)

        if "record_info" not in data:
            raise ValueError("Data must have a 'record_info' key.")
        if "date" not in data:
            raise ValueError("Data must have a 'date' key.")
        if "platform" not in data:
            raise ValueError("Data must have a 'platform' key.")
        if "database" not in data:
            raise ValueError("Data must have a 'database' key.")
        if "search_string" not in data:
            raise ValueError("Data must have a 'search_string' key.")

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
