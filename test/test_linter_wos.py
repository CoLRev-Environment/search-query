"""Web-of-Science linter unit tests."""
from collections.abc import Callable

import pytest

from search_query.constants import LinterMode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.linter_wos import WOSQueryStringLinter
from search_query.parser_wos import WOSParser
from search_query.utils import print_tokens

# ruff: noqa: E501
# flake8: noqa: E501


@pytest.fixture(scope="module")
def linter_factory() -> Callable[[str], WOSQueryStringLinter]:
    def _build_linter(query_str: str) -> WOSQueryStringLinter:
        parser = WOSParser(query_str)
        parser.tokenize()
        return WOSQueryStringLinter(parser)

    return _build_linter


def test_no_parentheses(linter_factory: Callable[[str], WOSQueryStringLinter]) -> None:
    linter = linter_factory("test query")
    linter.check_unbalanced_parentheses()
    assert len(linter.messages) == 0


def test_matched_parentheses(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("(test query)")
    linter.check_unbalanced_parentheses()
    assert len(linter.messages) == 0


def test_unmatched_opening_parenthesis(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("(test query")
    linter.check_unbalanced_parentheses()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F1001",
        "is_fatal": True,
        "details": "Unbalanced opening parenthesis",
        "label": "unbalanced-parentheses",
        "message": "Parentheses are unbalanced in the query",
        "position": (0, 1),
    }


def test_unmatched_closing_parenthesis(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("test query)")
    linter.check_unbalanced_parentheses()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F1001",
        "is_fatal": True,
        "details": "Unbalanced closing parenthesis",
        "label": "unbalanced-parentheses",
        "message": "Parentheses are unbalanced in the query",
        "position": (10, 11),
    }


def test_multiple_unmatched_parentheses(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("(test query))")
    linter.check_unbalanced_parentheses()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F1001",
        "is_fatal": True,
        "details": "Unbalanced closing parenthesis",
        "label": "unbalanced-parentheses",
        "message": "Parentheses are unbalanced in the query",
        "position": (12, 13),
    }


def test_nested_unmatched_parentheses(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("((test query)")
    linter.check_unbalanced_parentheses()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F1001",
        "is_fatal": True,
        "details": "Unbalanced opening parenthesis",
        "label": "unbalanced-parentheses",
        "message": "Parentheses are unbalanced in the query",
        "position": (0, 1),
    }


def test_two_operators_in_a_row(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("term1 AND OR")
    linter.check_invalid_token_sequences()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F1004",
        "is_fatal": True,
        "details": "Two operators in a row are not allowed.",
        "label": "invalid-token-sequence",
        "message": "The sequence of tokens is invalid.",
        "position": (6, 12),
    }


def test_two_search_fields_in_a_row(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("term1 au= ti=")
    linter.check_invalid_token_sequences()
    assert len(linter.messages) == 2
    assert linter.messages[0] == {
        "code": "F1004",
        "label": "invalid-token-sequence",
        "message": "The sequence of tokens is invalid.",
        "is_fatal": True,
        "details": "",
        "position": (6, 9),
    }


def test_missing_operator_between_term_and_parenthesis(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("term1 (query)")
    linter.check_invalid_token_sequences()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F1004",
        "is_fatal": True,
        "details": "",
        "label": "invalid-token-sequence",
        "message": "The sequence of tokens is invalid.",
        "position": (6, 7),
    }


def test_missing_operator_between_parentheses(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory(") (query)")
    linter.check_invalid_token_sequences()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F1004",
        "is_fatal": True,
        "details": "",
        "label": "invalid-token-sequence",
        "message": "The sequence of tokens is invalid.",
        "position": (2, 3),
    }


def test_missing_operator_between_term_and_search_field(
    linter_factory: Callable[[str], WOSQueryStringLinter]
) -> None:
    linter = linter_factory("term1 au=")
    linter.check_invalid_token_sequences()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F1004",
        "is_fatal": True,
        "details": "",
        "label": "invalid-token-sequence",
        "message": "The sequence of tokens is invalid.",
        "position": (6, 9),
    }


def test_near_distance_within_range() -> None:
    parser = WOSParser("term1 NEAR/10 term2")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_near_distance_in_range(max_value=15)
    assert len(linter.messages) == 0


def test_near_distance_out_of_range() -> None:
    parser = WOSParser("term1 NEAR/20 term2")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_near_distance_in_range(max_value=15)
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2007",
        "is_fatal": True,
        "details": "",
        "label": "near-distance-too-large",
        "message": "NEAR distance is too large (max: 15).",
        "position": (6, 13),
    }


def test_near_without_distance() -> None:
    parser = WOSParser("term1 NEAR term2")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_near_distance_in_range(max_value=15)
    assert len(linter.messages) == 0


def test_no_unsupported_wildcards() -> None:
    parser = WOSParser("term1 term2")
    linter = WOSQueryStringLinter(parser)
    linter.check_unsupported_wildcards()
    assert len(linter.messages) == 0


def test_unsupported_wildcards() -> None:
    parser = WOSParser("term1 !term2")
    linter = WOSQueryStringLinter(parser)
    linter.check_unsupported_wildcards()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2001",
        "label": "wildcard-unsupported",
        "message": "Unsupported wildcard in search string.",
        "is_fatal": True,
        "details": "",
        "position": (6, 7),
    }


def test_standalone_wildcard() -> None:
    parser = WOSParser('term1 AND "?"')
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_wildcards()
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2006",
        "is_fatal": True,
        "details": "",
        "label": "wildcard-standalone",
        "message": "Wildcard cannot be standalone.",
        "position": (10, 13),
    }


def test_wildcard_within_term() -> None:
    parser = WOSParser("term1 te?m2")
    linter = WOSQueryStringLinter(parser)
    linter.check_unsupported_wildcards()
    assert len(linter.messages) == 0


def test_no_unsupported_right_hand_wildcards() -> None:
    parser = WOSParser("term1 term2*")
    linter = WOSQueryStringLinter(parser)
    linter.check_unsupported_right_hand_wildcards(
        Token(value="term2*", type=TokenTypes.SEARCH_TERM, position=(6, 7)), 5
    )
    assert len(linter.messages) == 0


def test_unsupported_right_hand_wildcard_after_special_character() -> None:
    parser = WOSParser("term1 term2!*")
    linter = WOSQueryStringLinter(parser)
    linter.check_unsupported_right_hand_wildcards(
        Token(value="term2!*", type=TokenTypes.SEARCH_TERM, position=(6, 7)), 6
    )
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2005",
        "is_fatal": True,
        "details": "",
        "label": "wildcard-after-special-char",
        "message": "Wildcard cannot be preceded by special characters.",
        "position": (6, 7),
    }


def test_unsupported_right_hand_wildcard_with_less_than_three_characters() -> None:
    parser = WOSParser("te*")
    linter = WOSQueryStringLinter(parser)
    linter.check_unsupported_right_hand_wildcards(
        Token(value="te*", type=TokenTypes.SEARCH_TERM, position=(0, 2)), 2
    )
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2003",
        "is_fatal": True,
        "details": "",
        "label": "wildcard-right-short-length",
        "message": "Right-hand wildcard must preceded by at least three characters.",
        "position": (0, 2),
    }


def test_no_left_hand_wildcard() -> None:
    parser = WOSParser("term1 term2")
    linter = WOSQueryStringLinter(parser)
    linter.check_format_left_hand_wildcards(
        Token(value="term2", type=TokenTypes.SEARCH_TERM, position=(6, 11))
    )
    assert len(linter.messages) == 0


def test_valid_left_hand_wildcard() -> None:
    parser = WOSParser("term1 *term2")
    linter = WOSQueryStringLinter(parser)
    linter.check_format_left_hand_wildcards(
        Token(value="*term2", type=TokenTypes.SEARCH_TERM, position=(6, 12))
    )
    assert len(linter.messages) == 0


def test_invalid_left_hand_wildcard() -> None:
    parser = WOSParser("*te")
    linter = WOSQueryStringLinter(parser)
    linter.check_format_left_hand_wildcards(
        Token(value="*te", type=TokenTypes.SEARCH_TERM, position=(0, 2))
    )
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2004",
        "is_fatal": True,
        "details": "",
        "label": "wildcard-left-short-length",
        "message": "Left-hand wildcard must be preceded by at least three characters.",
        "position": (0, 2),
    }


def test_valid_issn_format() -> None:
    parser = WOSParser("1234-5678")
    linter = WOSQueryStringLinter(parser)
    linter.check_issn_isbn_format(
        Token(value="1234-5678", type=TokenTypes.SEARCH_TERM, position=(0, 3))
    )
    assert len(linter.messages) == 0


def test_invalid_issn_format() -> None:
    parser = WOSParser("1234-567")
    linter = WOSQueryStringLinter(parser)
    linter.check_issn_isbn_format(
        Token(value="1234-567", type=TokenTypes.SEARCH_TERM, position=(0, 3))
    )
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2008",
        "is_fatal": True,
        "details": "",
        "label": "isbn-format-invalid",
        "message": "Invalid ISBN format.",
        "position": (0, 3),
    }


def test_valid_isbn_format() -> None:
    parser = WOSParser("978-3-16-148410-0")
    linter = WOSQueryStringLinter(parser)
    linter.check_issn_isbn_format(
        Token(
            value="978-3-16-148410-0",
            type=TokenTypes.SEARCH_TERM,
            position=(0, 3),
        )
    )
    assert len(linter.messages) == 0


def test_invalid_isbn_format() -> None:
    parser = WOSParser("978-3-16-148410")
    linter = WOSQueryStringLinter(parser)
    linter.check_issn_isbn_format(
        Token(value="978-3-16-148410", type=TokenTypes.SEARCH_TERM, position=(0, 3))
    )
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2008",
        "is_fatal": True,
        "details": "",
        "label": "isbn-format-invalid",
        "message": "Invalid ISBN format.",
        "position": (0, 3),
    }


def test_valid_doi_format() -> None:
    parser = WOSParser("10.1000/xyz123")
    linter = WOSQueryStringLinter(parser)
    linter.check_doi_format(
        Token(value="10.1000/xyz123", type=TokenTypes.SEARCH_TERM, position=(0, 3))
    )
    assert len(linter.messages) == 0


def test_invalid_doi_format() -> None:
    parser = WOSParser("12.1000/xyz")
    linter = WOSQueryStringLinter(parser)
    linter.check_doi_format(
        Token(value="12.1000/xyz", type=TokenTypes.SEARCH_TERM, position=(0, 3))
    )
    assert len(linter.messages) == 1
    assert linter.messages[0] == {
        "code": "F2009",
        "is_fatal": True,
        "details": "",
        "label": "doi-format-invalid",
        "message": "Invalid DOI format.",
        "position": (0, 3),
    }


def test_handle_near_without_distance() -> None:
    parser = WOSParser("term1 NEAR term2")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_implicit_near()
    assert linter.messages[0] == {
        "code": "W0006",
        "is_fatal": False,
        "details": "",
        "label": "implicit-near-value",
        "message": "The value of NEAR operator is implicit",
        "position": (6, 10),
    }
    assert parser.tokens[1].value == "NEAR/15"


def test_handle_operator_lowercase() -> None:
    parser = WOSParser("term1 and term2")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_operator_capitalization()
    assert linter.messages[0] == {
        "code": "W0005",
        "is_fatal": False,
        "details": "",
        "label": "operator-capitalization",
        "message": "Operators should be capitalized",
        "position": (6, 9),
    }
    assert parser.tokens[1].value == "AND"


def test_year_format() -> None:
    parser = WOSParser("term1 and PY=202*")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_year_format()
    assert linter.messages[0] == {
        "code": "F2002",
        "is_fatal": True,
        "details": "",
        "label": "wildcard-in-year",
        "message": "Wildcard characters (*, ?, $) not supported in year search.",
        "position": (13, 17),
    }


def test_invalid_field() -> None:
    parser = WOSParser("term1 and IY=digital")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_fields()
    assert linter.messages[0] == {
        "code": "F2011",
        "label": "search-field-unsupported",
        "message": "Search field is not supported for this database",
        "is_fatal": True,
        "details": "Search field IY= at position (10, 13) is not supported.",
        "position": (10, 13),
    }


def test_year_span_violation() -> None:
    parser = WOSParser("term1 and PY=1900-2000")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_year_format()
    assert linter.messages[0] == {
        "code": "F2010",
        "is_fatal": True,
        "details": "",
        "label": "year-span-violation",
        "message": "Year span must be five or less.",
        "position": (13, 22),
    }
    assert parser.tokens[3].value == "1995-2000"


def test_check_search_fields_from_json_with_non_matching_field() -> None:
    parser = WOSParser("TI=digital", search_field_general="AB=")
    parser.tokenize()
    linter = WOSQueryStringLinter(parser)
    linter.check_search_fields_from_json()
    assert {
        "code": "E0002",
        "label": "search-field-contradiction",
        "message": "Contradictory search fields specified",
        "is_fatal": False,
        "details": "",
        "position": (0, 3),
    } in linter.messages


@pytest.mark.parametrize(
    "query_str, expected_message, expected_query",
    [
        (
            "TI=(term1 OR term2 AND term3)",
            "Operator changed at the same level (explicit parentheses are recommended)",
            "TI=(term1 OR TI=(term2 AND term3))",
        ),
        (
            "TI=term1 AND term2 OR term3",
            "Operator changed at the same level (explicit parentheses are recommended)",
            "(TI=(term1 AND term2) OR term3)",
        ),
        # TODO : proximity operators not yet handled by wos
        # (
        #     "term1 AND term2 NEAR term3",
        #     "Operator changed at the same level (explicit parentheses are recommended)",
        #     ""
        # ),
        # (
        #     "term1 NEAR/5 term2 AND term3",
        #     "Operator changed at the same level (explicit parentheses are recommended)",
        #     ""
        # ),
    ],
)
def test_implicit_precedence(
    query_str: str, expected_message: str, expected_query: str
) -> None:
    parser = WOSParser(query_str, mode=LinterMode.NONSTRICT)
    query = parser.parse()
    print_tokens(parser.tokens)

    assert expected_query == query.to_string(syntax="wos")

    assert len(parser.linter.messages) == 1
    msg = parser.linter.messages[0]

    assert msg["code"] == "W0007"
    assert msg["label"] == "implicit-precedence"
    assert msg["message"] == expected_message
    assert msg["is_fatal"] is False
    assert msg["details"] == ""
