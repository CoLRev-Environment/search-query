#!/usr/bin/env python3
"""SaveFile to json format"""
import datetime
import json
import typing
from pathlib import Path


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments
class SaveFile:
    """SaveFile model."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        filename: str,
        query_str: str,
        syntax: str,
        platform: str,
        authors: typing.List[dict],
        parent_directory: str,
        coder_initials: str = "",
        comment: str = "",
    ) -> None:
        """
        Initializes the SaveFile object and immediately saves the query to a JSON file.
        """
        self.filename = filename
        self.query_str = query_str
        self.syntax = syntax
        self.platform = platform
        self.authors = authors
        self.parent_directory = parent_directory
        self.coder_initials = coder_initials
        self.comment = comment

        assert Path(self.parent_directory).exists()

        # Save the file immediately upon initialization
        self.save()

    def save(self) -> None:
        """Saves the search query to a JSON file in the appropriate directory."""
        # Ensure parent directory exists
        target_directory = Path(self.parent_directory) / self.syntax
        target_directory.mkdir(exist_ok=True)

        # Define the full file path
        file_path = target_directory / self.filename

        data = {
            "query_string": self.query_str,
            "syntax": self.syntax,
            "platform": self.platform,
            "authors": self.authors,
            "coder_initials": self.coder_initials,
            "comment": self.comment,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        # Save JSON file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
