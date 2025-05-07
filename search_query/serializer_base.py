#!/usr/bin/env python3
"""Pubmed serializer."""
from __future__ import annotations

import typing
from abc import ABC
from abc import abstractmethod


if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


# pylint: disable=too-few-public-methods
class StringSerializer(ABC):
    """Base class for query serializers."""

    @abstractmethod
    def to_string(self, query: Query) -> str:
        """Convert the query to a string.

        Args:
            query: The query to convert.

        Returns:
            The string representation of the query.
        """
