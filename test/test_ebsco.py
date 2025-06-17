#!/usr/bin/env python
"""Tests for search query translation."""
from typing import List
from typing import Tuple

import pytest

from search_query.constants import Colors
from search_query.constants import LinterMode
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.ebsco.linter import EBSCOQueryStringLinter
from search_query.ebsco.parser import EBSCOParser
from search_query.ebsco.serializer import to_string_ebsco
from search_query.query import SearchField
from search_query.query_and import AndQuery
from search_query.query_near import NEARQuery
from search_query.query_or import OrQuery
from search_query.query_term import Term

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, expected_tokens",
    [
        (
            'TI "Artificial Intelligence" AND AB Future NOT AB Past',
            [
                Token(value="TI", type=TokenTypes.FIELD, position=(0, 2)),
                Token(
                    value='"Artificial Intelligence"',
                    type=TokenTypes.SEARCH_TERM,
                    position=(3, 28),
                ),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(29, 32)),
                Token(value="AB", type=TokenTypes.FIELD, position=(33, 35)),
                Token(value="Future", type=TokenTypes.SEARCH_TERM, position=(36, 42)),
                Token(value="NOT", type=TokenTypes.LOGIC_OPERATOR, position=(43, 46)),
                Token(value="AB", type=TokenTypes.FIELD, position=(47, 49)),
                Token(value="Past", type=TokenTypes.SEARCH_TERM, position=(50, 54)),
            ],
        ),
        (
            "Artificial N2 Intelligence",
            [
                Token(
                    value="Artificial", type=TokenTypes.SEARCH_TERM, position=(0, 10)
                ),
                Token(
                    value="N2", type=TokenTypes.PROXIMITY_OPERATOR, position=(11, 13)
                ),
                Token(
                    value="Intelligence", type=TokenTypes.SEARCH_TERM, position=(14, 26)
                ),
            ],
        ),
        (
            # Note: NEAR/2 is invalid, but we match it to give better error messages and handle it gracefully
            "arrest* NEAR/2 (record* OR history* OR police)",
            [
                Token(
                    value="arrest*",
                    type=TokenTypes.SEARCH_TERM,
                    position=(0, 7),
                ),
                Token(
                    value="NEAR/2",
                    type=TokenTypes.PROXIMITY_OPERATOR,
                    position=(8, 14),
                ),
                Token(
                    value="(",
                    type=TokenTypes.PARENTHESIS_OPEN,
                    position=(15, 16),
                ),
                Token(
                    value="record*",
                    type=TokenTypes.SEARCH_TERM,
                    position=(16, 23),
                ),
                Token(
                    value="OR",
                    type=TokenTypes.LOGIC_OPERATOR,
                    position=(24, 26),
                ),
                Token(
                    value="history*",
                    type=TokenTypes.SEARCH_TERM,
                    position=(27, 35),
                ),
                Token(
                    value="OR",
                    type=TokenTypes.LOGIC_OPERATOR,
                    position=(36, 38),
                ),
                Token(
                    value="police",
                    type=TokenTypes.SEARCH_TERM,
                    position=(39, 45),
                ),
                Token(
                    value=")",
                    type=TokenTypes.PARENTHESIS_CLOSED,
                    position=(45, 46),
                ),
            ],
        ),
        (
            "TI RN OR AB RN",
            [
                Token(value="TI", type=TokenTypes.FIELD, position=(0, 2)),
                Token(value="RN", type=TokenTypes.SEARCH_TERM, position=(3, 5)),
                Token(value="OR", type=TokenTypes.LOGIC_OPERATOR, position=(6, 8)),
                Token(value="AB", type=TokenTypes.FIELD, position=(9, 11)),
                Token(value="RN", type=TokenTypes.SEARCH_TERM, position=(12, 14)),
            ],
        ),
        # (
        #     '(DE "Persuasive Communication) OR (DE "Collaboration")',
        #     [
        #     ]
        # )
    ],
)
def test_tokenization(
    query_string: str, expected_tokens: List[Tuple[str, str, Tuple[int, int]]]
) -> None:
    """Test EBSCO parser tokenization."""
    print(query_string)
    parser = EBSCOParser(query_string, search_field_general="")
    parser.tokenize()

    actual_tokens = parser.tokens
    parser.print_tokens()
    assert actual_tokens == expected_tokens


@pytest.mark.parametrize(
    "tokens, expected_codes, description",
    [
        (
            [
                Token("AND", TokenTypes.LOGIC_OPERATOR, (0, 3)),
                Token("diabetes", TokenTypes.SEARCH_TERM, (4, 12)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Cannot start with LOGIC_OPERATOR",
        ),
        (
            [
                Token("diabetes", TokenTypes.SEARCH_TERM, (0, 8)),
                Token("AND", TokenTypes.LOGIC_OPERATOR, (9, 12)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Cannot end with LOGIC_OPERATOR",
        ),
        (
            [
                Token("diabetes", TokenTypes.SEARCH_TERM, (0, 8)),
                Token("hypertension", TokenTypes.SEARCH_TERM, (9, 20)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Missing operator between terms",
        ),
        (
            [
                Token("(", TokenTypes.PARENTHESIS_OPEN, (0, 1)),
                Token(")", TokenTypes.PARENTHESIS_CLOSED, (1, 2)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Empty parenthesis",
        ),
        (
            [
                Token("ti", TokenTypes.SEARCH_TERM, (0, 2)),
                Token("(", TokenTypes.PARENTHESIS_OPEN, (3, 4)),
            ],
            [QueryErrorCode.SEARCH_FIELD_UNSUPPORTED.label],
            "Search field is not supported (must be upper case)",
        ),
        (
            [
                Token("diabetes", TokenTypes.SEARCH_TERM, (0, 8)),
                Token("TI", TokenTypes.FIELD, (9, 11)),
                Token("insulin", TokenTypes.SEARCH_TERM, (12, 19)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Invalid search field position",
        ),
        (
            [
                Token("TI", TokenTypes.FIELD, (0, 2)),
                Token("diabetes", TokenTypes.SEARCH_TERM, (3, 11)),
            ],
            [],
            "Valid field and term",
        ),
    ],
)
def test_invalid_token_sequences(
    tokens: list, expected_codes: list, description: str
) -> None:
    print(tokens)
    linter = EBSCOQueryStringLinter(query_str="")
    linter.tokens = tokens
    linter.check_invalid_token_sequences()

    actual_codes = [msg["label"] for msg in linter.messages]
    if expected_codes:
        for message in linter.messages:
            if message["label"] in expected_codes:
                assert message.get("details", "") == description, (
                    f"Expected description '{description}' for code '{message['label']}', "
                    f"but got '{message.get('details', '')}'"
                )
        for code in expected_codes:
            assert code in actual_codes, f"Expected code '{code}' in {actual_codes}"
    else:
        assert (
            linter.messages == []
        ), f"Expected no messages, but got: {linter.messages}"


@pytest.mark.parametrize(
    "query_string, messages",
    [
        (
            "(Artificial Intelligence AND Future",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(0, 1)],
                    "details": "Unbalanced opening parenthesis",
                }
            ],
        ),
        (
            "TI AND Artificial Intelligence",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(3, 6)],
                    "details": "Invalid operator position",
                }
            ],
        ),
        ("TI Artificial Intelligence AND AB Future", []),
        (
            "AI governance OR AB Future",
            [
                {
                    "code": "F2011",
                    "label": "search-field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": [(0, 2)],
                    "details": "Search field AI at position (0, 2) is not supported. Supported fields for PLATFORM.EBSCO: TI|AB|TP|TX|AU|SU|SO|IS|IB|LA|KW|DE|MH|ZY|ZU",
                }
            ],
        ),
        (
            'AI "governance" OR AB Future',
            [
                {
                    "code": "F2011",
                    "label": "search-field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": [(0, 2)],
                    "details": "Search field AI at position (0, 2) is not supported. Supported fields for PLATFORM.EBSCO: TI|AB|TP|TX|AU|SU|SO|IS|IB|LA|KW|DE|MH|ZY|ZU",
                }
            ],
        ),
        (
            "ti (ehealth OR mhealth)",
            [
                {
                    "code": "F2011",
                    "label": "search-field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": [(0, 2)],
                    "details": "Search field is not supported (must be upper case)",
                }
            ],
        ),
        (
            'MH "sleep" OR MH "sleep disorders"',
            [
                {
                    "code": "W0004",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(3, 10), (17, 34)],
                    "details": 'Results for term "sleep disorders" are contained in the more general search for "sleep" (both terms are connected with OR). Therefore, the term "sleep disorders" is redundant.',
                }
            ],
        ),
        (
            # No message: ZY "sudan" does not match the pattern for ZY "south sudan"
            '(ZY "sudan" OR ZY "south sudan") AND TI "context of vegetarians"',
            [],
        ),
        (
            "bias OR OR politics",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(8, 10)],
                    "details": "Cannot have two consecutive operators",
                }
            ],
        ),
        (
            "*ology",
            [
                {
                    "code": "F2001",
                    "label": "wildcard-unsupported",
                    "message": "Unsupported wildcard in search string.",
                    "is_fatal": True,
                    "position": [(0, 1)],
                    "details": "Wildcard not allowed at the beginning of a term.",
                }
            ],
        ),
        (
            "f??*",
            [
                {
                    "code": "F2001",
                    "label": "wildcard-unsupported",
                    "message": "Unsupported wildcard in search string.",
                    "is_fatal": True,
                    "position": [(0, 4)],
                    "details": "Invalid wildcard use: only one leading literal character found. When a wildcard appears within the first four characters, at least two literal (non-wildcard) characters must be present in that span.",
                }
            ],
        ),
        (
            "f*tal",
            [
                {
                    "code": "F2001",
                    "label": "wildcard-unsupported",
                    "message": "Unsupported wildcard in search string.",
                    "is_fatal": True,
                    "position": [(0, 5)],
                    "details": "Do not use * in the second position followed by additional letters. Use ? or # instead (e.g., f?tal).",
                }
            ],
        ),
        (
            "colo#r",
            [],
        ),
        (
            "pediatric*",
            [],
        ),
        (
            "tumor*",
            [],
        ),
        (
            "education*",
            [],
        ),
        (
            "f#tal",
            [],
        ),
        (
            "f?tal",
            [],
        ),
    ],
)
def test_linter(query_string: str, messages: list) -> None:
    print(query_string)
    parser = EBSCOParser(query_string, search_field_general="")
    try:
        parser.parse()
    except Exception:
        pass

    print(query_string)
    parser.tokenize()
    print(parser.tokens)
    parser.print_tokens()
    print(parser.linter.messages)

    assert parser.linter.messages == messages


@pytest.mark.parametrize(
    "query_string, search_field_general, messages",
    [
        (
            "TI Artificial Intelligence AND AB Future",
            "AB",
            [
                {
                    "code": "W0002",
                    "label": "search-field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "",
                }
            ],
        ),
        (
            "governance[tiab]",
            "",
            [
                {
                    "code": "F1010",
                    "label": "invalid-syntax",
                    "message": "Query contains invalid syntax",
                    "is_fatal": True,
                    "position": [(10, 16)],
                    "details": "EBSCOHOst fields must be before search terms and without brackets, e.g. AB robot or TI monitor. '[tiab]' is invalid.",
                }
            ],
        ),
        (
            "Artificial intelligence and Future",
            "",
            [
                {
                    "code": "W0005",
                    "label": "operator-capitalization",
                    "message": "Operators should be capitalized",
                    "is_fatal": False,
                    "position": [(24, 27)],
                    "details": "",
                }
            ],
        ),
        (
            "arrest* NEAR/2 (record* OR history* OR police)",
            "",
            [
                {
                    "code": "E0005",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(8, 14)],
                    "details": "Operator NEAR/2 is not supported by EBSCO. Must be N2 instead.",
                }
            ],
        ),
        ("arrest* N2 (record* OR history* OR police)", "", []),
        (
            "arrest* WITHIN/2 (record* OR history* OR police)",
            "",
            [
                {
                    "code": "E0005",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(8, 16)],
                    "details": "Operator WITHIN/2 is not supported by EBSCO. Must be W2 instead.",
                }
            ],
        ),
        ("arrest* W2 (record* OR history* OR police)", "", []),
    ],
)
def test_linter_general_search_field(
    query_string: str, search_field_general: str, messages: list
) -> None:
    print(query_string)
    parser = EBSCOParser(
        query_string, search_field_general=search_field_general, mode=LinterMode.STRICT
    )
    try:
        parser.parse()
    except Exception:
        pass
    print(parser.linter.messages)
    parser.print_tokens()
    assert parser.linter.messages == messages
    print(parser.linter.messages)


@pytest.mark.parametrize(
    "query_str, expected_translation",
    [
        (
            'TI example AND (AU "John Doe" OR AU "John Wayne")',
            'AND[example[TI], OR["John Doe"[AU], "John Wayne"[AU]]]',
        ),
        # Implicit precedence / artificial parentheses
        (
            'TI "Artificial Intelligence" AND AB Future NOT AB Past',
            'AND["Artificial Intelligence"[TI], NOT[Future[AB], Past[AB]]]',
        ),
        (
            'TI "Artificial Intelligence" NOT AB Future AND AB Past',
            'AND[NOT["Artificial Intelligence"[TI], Future[AB]], Past[AB]]',
        ),
        (
            'TI "AI" OR AB Robots AND AB Ethics',
            'OR["AI"[TI], AND[Robots[AB], Ethics[AB]]]',
        ),
        (
            'TI "AI" AND AB Robots OR AB Ethics',
            'OR[AND["AI"[TI], Robots[AB]], Ethics[AB]]',
        ),
        (
            'TI "AI" NOT AB Robots OR AB Ethics',
            'OR[NOT["AI"[TI], Robots[AB]], Ethics[AB]]',
        ),
        (
            'TI "AI" AND (AB Robots OR AB Ethics NOT AB Bias) OR SU "Technology"',
            'OR[AND["AI"[TI], OR[Robots[AB], NOT[Ethics[AB], Bias[AB]]]], "Technology"[SU]]',
        ),
        (
            'TI "Robo*" OR AB Robots AND AB Ethics NOT AB Bias OR SU "Technology"',
            'OR["Robo*"[TI], AND[Robots[AB], NOT[Ethics[AB], Bias[AB]]], "Technology"[SU]]',
        ),
        (
            'TX ("digital transformation" N5 "organizational change")',
            'NEAR/5[TX]["digital transformation"[TX], "organizational change"[TX]]',
        ),
        (
            'TX ("digital transformation" W5 "organizational change")',
            'WITHIN/5[TX]["digital transformation"[TX], "organizational change"[TX]]',
        ),
    ],
)
def test_parser(query_str: str, expected_translation: str) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = EBSCOParser(
        query_str=query_str,
        search_field_general="",
        mode="",
    )
    query_tree = parser.parse()

    # print("--------------------")
    # print("Tokens: \n")
    # parser.print_tokens()

    assert expected_translation == query_tree.to_generic_string(), print(
        query_tree.to_generic_string()
    )


def test_leaf_node_with_field() -> None:
    query = Term(
        value="diabetes",
        search_field=SearchField("TI"),
        platform="ebscohost",
    )
    assert to_string_ebsco(query) == "TI diabetes"


def test_leaf_node_without_field() -> None:
    query = Term(value="diabetes")
    assert to_string_ebsco(query) == "diabetes"


def test_boolean_query_with_two_terms() -> None:
    query = AndQuery(
        children=[
            Term(
                value="diabetes",
                search_field=SearchField("TI"),
                platform="ebscohost",
            ),
            Term(
                value="insulin",
                search_field=SearchField("TI"),
                platform="ebscohost",
            ),
        ],
        platform="ebscohost",
    )
    assert to_string_ebsco(query) == "(TI diabetes AND TI insulin)"


def test_nested_boolean_with_field() -> None:
    inner = AndQuery(
        children=[
            Term(value="diabetes"),
            Term(value="insulin"),
        ],
        platform="ebscohost",
    )
    outer = OrQuery(
        search_field=SearchField("AB"),
        children=[inner, Term(value="therapy")],
        platform="ebscohost",
    )
    # Test search field propagation and parentheses
    assert to_string_ebsco(outer) == "AB ((diabetes AND insulin) OR therapy)"


def test_proximity_near_operator() -> None:
    query = NEARQuery(
        value="NEAR",
        distance=5,
        children=[
            Term(value="diabetes", platform="ebscohost"),
            Term(value="therapy", platform="ebscohost"),
        ],
        platform="ebscohost",
    )
    assert to_string_ebsco(query) == "(diabetes N5 therapy)"


def test_proximity_within_operator_with_field() -> None:
    query = NEARQuery(
        value="WITHIN",
        distance=3,
        search_field=SearchField("AB"),
        children=[
            Term(value="insulin", platform="ebscohost"),
            Term(value="resistance", platform="ebscohost"),
        ],
        platform="ebscohost",
    )
    assert to_string_ebsco(query) == "AB (insulin W3 resistance)"


def test_proximity_missing_distance_raises() -> None:
    with pytest.raises(ValueError, match="NEAR operator requires a distance"):
        NEARQuery(value="NEAR", children=["AI", "health"], distance=None, platform="ebscohost")  # type: ignore
