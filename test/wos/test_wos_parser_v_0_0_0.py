"""Tests for WOSParser_v0_0_0"""

from search_query.wos.v_0_0_0.parser import WOSParser_v0_0_0


def test_deprecated_fields_supported() -> None:
    parser = WOSParser_v0_0_0("FN=example AND DE=test")
    parser.parse()
    assert parser.linter.messages == []
