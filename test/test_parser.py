#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.parser import get_platform


# pylint: disable=line-too-long
# flake8: noqa: E501


def test_get_platform(query_setup: dict) -> None:
    assert get_platform("pubmed") == "pubmed"
    assert get_platform("wos") == "wos"
    assert get_platform("web of science") == "wos"
    assert get_platform("ebsco") == "ebscohost"
    assert get_platform("ebscohost") == "ebscohost"

    with pytest.raises(ValueError):
        get_platform("unknown_platform")
