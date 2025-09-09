"""Tests for WOSParser_v0"""
from search_query.wos.v_0.parser import WOSParser_v0


def test_deprecated_fields_supported() -> None:
    parser = WOSParser_v0("FN=example AND DE=test")
    parser.parse()
    assert parser.linter.messages == []
