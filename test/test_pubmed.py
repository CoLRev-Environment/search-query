#!/usr/bin/env python
"""Tests for Pubmed search query parser."""
from typing import Tuple

import pytest

from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import SearchQueryException
from search_query.linter_pubmed import PubmedQueryStringLinter
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
def test_tokenization_pubmed(query_str: str, expected_tokens: list) -> None:
    pubmed_parser = PubmedParser(query_str, "")
    pubmed_parser.tokenize()
    assert pubmed_parser.tokens == expected_tokens, print(pubmed_parser.tokens)


@pytest.mark.parametrize(
    "query_str, expected_translation",
    [
        (
            '(eHealth[Title/Abstract] OR "eHealth"[MeSH Terms]) AND Review[Publication Type]',
            # TODO : should the operators have search_field?
            'AND[all][OR[all][OR[all][eHealth[ti], eHealth[ab]], "eHealth"[mh]], Review[pt]]',
        )
    ],
)
def test_parser_pubmed(query_str: str, expected_translation: str) -> None:
    pubmed_parser = PubmedParser(query_str, "")
    query_tree = pubmed_parser.parse()
    assert expected_translation == query_tree.to_string(), print(query_tree.to_string())


@pytest.mark.parametrize(
    "query_str, error, position",
    [
        (
            '("health tracking" OR "remote monitoring") AND (("mobile application" OR "wearable device")',
            QueryErrorCode.UNBALANCED_PARENTHESES,
            (47, 48),
        ),
        (
            '("health tracking" OR "remote monitoring")) AND ("mobile application" OR "wearable device")',
            QueryErrorCode.UNBALANCED_PARENTHESES,
            (42, 43),
        ),
        (
            '"health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")',
            QueryErrorCode.IMPLICIT_PRECEDENCE,
            (18, 20),
        ),
        (
            '"healthcare" AND "Industry 4.0"',
            QueryErrorCode.INVALID_CHARACTER,
            (17, 31),
        ),
        (
            '"health tracking" AND AI*',
            QueryErrorCode.INVALID_WILDCARD_USE,
            (22, 25),
        ),
        (
            '("eHealth" OR "digital health")[tiab]',
            QueryErrorCode.INVALID_TOKEN_SEQUENCE,
            (31, 37),
        ),
        (
            '"eHealth"[tiab] "digital health"[tiab]',
            QueryErrorCode.INVALID_TOKEN_SEQUENCE,
            (9, 32),
        ),
        (
            '("health tracking" OR "remote monitoring")("mobile application" OR "wearable device")',
            QueryErrorCode.INVALID_TOKEN_SEQUENCE,
            (41, 43),
        ),
        (
            "digital health[tiab:~5]",
            QueryErrorCode.INVALID_PROXIMITY_USE,
            (14, 23),
        ),
        (
            '"digital health"[tiab:~0.5]',
            QueryErrorCode.INVALID_PROXIMITY_USE,
            (16, 27),
        ),
        (
            '"digital health"[tiab:~5] OR "eHealth"[tiab:~5]',
            QueryErrorCode.INVALID_PROXIMITY_USE,
            (38, 47),
        ),
        (
            '("remote monitoring" NOT "in-person") AND "health outcomes"',
            QueryErrorCode.NESTED_NOT_QUERY,
            (1, 36),
        ),
        (
            '"device" AND ("wearable device" AND "health tracking")',
            QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
            (0, 8),
        ),
        (
            '("device" OR ("mobile application" OR "wearable device")) AND "health tracking"',
            QueryErrorCode.QUERY_STRUCTURE_COMPLEX,
            (38, 55),
        ),
        (
            '"eHealth"[ab]',
            QueryErrorCode.SEARCH_FIELD_UNSUPPORTED,
            (9, 13),
        ),
    ],
)
def test_linter_pubmed(
    query_str: str,
    error: QueryErrorCode,
    position: Tuple,
) -> None:
    pubmed_parser = PubmedParser(query_str, search_field_general="")
    try:
        pubmed_parser.parse()
    except SearchQueryException:
        pass

    assert any(
        message["code"] == error.code and message["position"] == position
        for message in pubmed_parser.linter.messages
    ), print(pubmed_parser.linter.messages)


@pytest.mark.parametrize(
    "query_string, expected_output_string",
    [
        (
            '"health tracking" OR "remote monitoring" AND "wearable device"',
            '"health tracking" OR ( "remote monitoring" AND "wearable device" ) ',
        ),
        (
            '"AI" AND "robotics" OR "ethics"',
            '( "AI" AND "robotics" ) OR "ethics" ',
        ),
        (
            '"AI" OR "robotics" AND "ethics"',
            '"AI" OR ( "robotics" AND "ethics" ) ',
        ),
        (
            '"AI" NOT "robotics" OR "ethics"',
            '( "AI" NOT "robotics" ) OR "ethics" ',
        ),
        (
            '"digital health" AND ("apps" OR "wearables" NOT "privacy") OR "ethics"',
            '( "digital health" AND ( "apps" OR ( "wearables" NOT "privacy" ) ) ) OR "ethics" ',
        ),
        (
            '"eHealth" OR "digital health" AND "bias" NOT "equity" OR "policy"',
            '"eHealth" OR ( "digital health" AND ( "bias" NOT "equity" ) ) OR "policy" ',
        ),
    ],
)
def test_add_artificial_parentheses_for_operator_precedence_pubmed(
    query_string: str, expected_output_string: str
) -> None:
    """Test PubMed parser normalization for operator precedence via artificial parentheses."""
    pubmed_parser = PubmedParser(query_string, "")
    pubmed_parser.tokenize()

    linter = PubmedQueryStringLinter(pubmed_parser)
    linter.validate_tokens()

    actual_tokens = pubmed_parser.tokens
    actual_string = "".join(f"{token.value} " for token in actual_tokens)

    print("actual string: " + actual_string)
    assert actual_string == expected_output_string
