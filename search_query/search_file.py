#!/usr/bin/env python3
"""SearchHistoryFile parser."""
from __future__ import annotations

import typing

from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pydantic import Field

# pylint: disable=too-few-public-methods
# pylint: disable=no-self-argument


class Author(BaseModel):
    """Author model."""

    name: str
    email: typing.Optional[str] = Field(regex=r"^\S+@\S+\.\S+$")
    ORCID: typing.Optional[str] = Field(regex=r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$")


class Date(BaseModel):
    """Date model."""

    data_entry: typing.Optional[str] = Field(regex=r"^\d{4}\.\d{2}\.\d{2}$")
    strategy_exported: typing.Optional[str] = Field(regex=r"^\d{4}\.\d{2}\.\d{2}$")
    search_conducted: typing.Optional[str] = Field(regex=r"^\d{4}\.\d{2}\.\d{2}$")
    search_updated_1: typing.Optional[str] = Field(regex=r"^\d{4}\.\d{2}\.\d{2}$")


class SearchHistoryFile(BaseModel):
    """SearchHistoryFile model."""

    record_info: typing.Dict[str, str]
    authors: typing.List[Author]
    date: Date
    platform: str
    database: typing.List[str]
    search_string: str

    parsed: typing.Optional[dict]

    # string_name: str
    # keywords: str
    # related_records: str
    # parent_record: str
    # database_time_coverage: str
    # search_language: str
    # settings: str
    # quality_assurance: str
    # validation_report: str
    # peer_review: str
    # description: str
    # review_question: str
    # review_type: str
    # linked_protocol: str
    # linked_report: str
