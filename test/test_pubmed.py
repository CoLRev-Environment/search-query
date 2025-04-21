#!/usr/bin/env python
"""Tests for Pubmed search query parser."""
import pytest

from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import SearchQueryException
from search_query.parser_pubmed import PubmedParser

# to run (from top-level dir): pytest test/test_parser_pubmed.py

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_str, expected_tokens",
    [
        (
            '("health tracking" [tw] OR"remote monitoring"[tw])AND wearable device[tw]NOT Comment[pt]',
            [
                Token(value="(", type=TokenTypes.PARENTHESIS_OPEN, position=(0, 1)),
                Token(
                    value='"health tracking"',
                    type=TokenTypes.SEARCH_TERM,
                    position=(1, 18),
                ),
                Token(value="[tw]", type=TokenTypes.FIELD, position=(19, 23)),
                Token(value="OR", type=TokenTypes.LOGIC_OPERATOR, position=(24, 26)),
                Token(
                    value='"remote monitoring"',
                    type=TokenTypes.SEARCH_TERM,
                    position=(26, 45),
                ),
                Token(value="[tw]", type=TokenTypes.FIELD, position=(45, 49)),
                Token(value=")", type=TokenTypes.PARENTHESIS_CLOSED, position=(49, 50)),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(50, 53)),
                Token(
                    value="wearable device",
                    type=TokenTypes.SEARCH_TERM,
                    position=(54, 69),
                ),
                Token(value="[tw]", type=TokenTypes.FIELD, position=(69, 73)),
                Token(value="NOT", type=TokenTypes.LOGIC_OPERATOR, position=(73, 76)),
                Token(value="Comment", type=TokenTypes.SEARCH_TERM, position=(77, 84)),
                Token(value="[pt]", type=TokenTypes.FIELD, position=(84, 88)),
            ],
        )
    ],
)
def test_tokenization(query_str: str, expected_tokens: list) -> None:
    parser = PubmedParser(query_str, "")
    parser.tokenize()
    assert parser.tokens == expected_tokens, print(parser.tokens)


@pytest.mark.parametrize(
    "query_str, expected_translation",
    [
        (
            '(eHealth[Title/Abstract] OR "eHealth"[MeSH Terms]) AND Review[Publication Type]',
            # TODO : should the operators have search_field?
            'AND[all][OR[all][OR[all][eHealth[ti], eHealth[ab]], "eHealth"[mh]], Review[pt]]',
        ),
        # Artificial parentheses:
        (
            '"health tracking" OR "remote monitoring" AND "wearable device"',
            'OR[all]["health tracking"[all], AND[all]["remote monitoring"[all], "wearable device"[all]]]',
        ),
        (
            '"AI" AND "robotics" OR "ethics"',
            'OR[all][AND[all]["AI"[all], "robotics"[all]], "ethics"[all]]',
        ),
        (
            '"AI" OR "robotics" AND "ethics"',
            'OR[all]["AI"[all], AND[all]["robotics"[all], "ethics"[all]]]',
        ),
        # TODO : check (invalid queries)?
        # (
        #     '"AI" NOT "robotics" OR "ethics"',
        #     '( "AI" NOT "robotics" ) OR "ethics" ',
        # ),
        # (
        #     '"digital health" AND ("apps" OR "wearables" NOT "privacy") OR "ethics"',
        #     '( "digital health" AND ( "apps" OR ( "wearables" NOT "privacy" ) ) ) OR "ethics" ',
        # ),
        # (
        #     '"eHealth" OR "digital health" AND "bias" NOT "equity" OR "policy"',
        #     '"eHealth" OR ( "digital health" AND ( "bias" NOT "equity" ) ) OR "policy" ',
        # ),
    ],
)
def test_parser(query_str: str, expected_translation: str) -> None:
    parser = PubmedParser(query_str)
    query = parser.parse()
    assert expected_translation == query.to_string(), print(query.to_string())


@pytest.mark.parametrize(
    "query_str, messages",
    [
        (
            '("health tracking" OR "remote monitoring") AND (("mobile application" OR "wearable device")',
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (47, 48),
                    "details": "Unbalanced opening parenthesis",
                }
            ],
        ),
        (
            '("health tracking" OR "remote monitoring")) AND ("mobile application" OR "wearable device")',
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (42, 43),
                    "details": "Unbalanced closing parenthesis",
                }
            ],
        ),
        (
            '"health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")',
            [
                {
                    "code": "W0007",
                    "label": "implicit-precedence",
                    "message": "Operator changed at the same level (explicit parentheses are recommended)",
                    "is_fatal": False,
                    "position": (18, 20),
                    "details": "",
                }
            ],
        ),
        # Note: corresponds to the search for "Industry 4 0" (replaced dot with space)
        (
            '"healthcare" AND "Industry 4.0"',
            [
                {
                    "code": "W0010",
                    "label": "character-replacement",
                    "message": "Character replacement",
                    "is_fatal": False,
                    "position": (28, 29),
                    "details": "Character '.' in search term will be replaced with whitespace (see PubMed character conversions in https://pubmed.ncbi.nlm.nih.gov/help/)",
                }
            ],
        ),
        (
            '"health tracking" AND AI*',
            [
                {
                    "code": "E0006",
                    "label": "invalid-wildcard-use",
                    "message": "Invalid use of the wildcard operator *",
                    "is_fatal": False,
                    "position": (22, 25),
                    "details": "",
                }
            ],
        ),
        (
            '("eHealth" OR "digital health")[tiab]',
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (31, 37),
                    "details": "Invalid search field position",
                }
            ],
        ),
        (
            '"eHealth"[tiab] "digital health"[tiab]',
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (9, 32),
                    "details": "Missing operator",
                }
            ],
        ),
        (
            '("health tracking" OR "remote monitoring")("mobile application" OR "wearable device")',
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (41, 43),
                    "details": "Missing operator",
                }
            ],
        ),
        (
            "digital health[tiab:~5]",
            [
                {
                    "code": "E0005",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator :~",
                    "is_fatal": False,
                    "position": (14, 23),
                    "details": "When using proximity operators, search terms consisting of 2 or more words (i.e., digital health) must be enclosed in double quotes",
                }
            ],
        ),
        (
            '"digital health"[tiab:~0.5]',
            [
                {
                    "code": "E0005",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator :~",
                    "is_fatal": False,
                    "position": (16, 27),
                    "details": "Proximity value '0.5' is not a digit",
                }
            ],
        ),
        (
            '"digital health"[tiab:~5] OR "eHealth"[tiab:~5]',
            [],
        ),
        (
            '("remote monitoring" NOT "in-person") AND "health outcomes"',
            [
                {
                    "code": "F1008",
                    "label": "nested-not-query",
                    "message": "Nesting of NOT operator is not supported for this database",
                    "is_fatal": True,
                    "position": (1, 36),
                    "details": "",
                }
            ],
        ),
        (
            '"device" AND ("wearable device" AND "health tracking")',
            [
                {
                    "code": "W0004",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": (0, 8),
                    "details": "",
                }
            ],
        ),
        (
            '("device" OR ("mobile application" OR "wearable device")) AND "health tracking"',
            [
                {
                    "code": "W0004",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": (38, 55),
                    "details": "",
                }
            ],
        ),
        (
            '"eHealth"[ab]',
            [
                {
                    "code": "F2011",
                    "label": "search-field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": (9, 13),
                    "details": "",
                },
            ],
        ),
    ],
)
def test_linter(
    query_str: str,
    messages: list,
) -> None:
    parser = PubmedParser(query_str, search_field_general="")
    try:
        parser.parse()
    except SearchQueryException:
        pass
    print(query_str)
    print(parser.linter.messages)
    assert messages == parser.linter.messages
