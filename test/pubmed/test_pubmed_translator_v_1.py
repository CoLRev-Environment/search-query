#!/usr/bin/env python
"""Tests for PubMedTranslator_v1"""
import pytest

from search_query.pubmed.v_1.parser import PubMedParser_v1
from search_query.pubmed.v_1.translator import PubMedTranslator_v1

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_str, expected_generic",
    [
        (
            "eHealth[ti]",
            "eHealth[title]",
        ),
        (
            "eHealth[tiab]",
            "OR[eHealth[abstract], eHealth[title]]",
        ),
        (
            "eHealth[tiab] OR mHealth[tiab]",
            "OR[eHealth[title], mHealth[title], eHealth[abstract], mHealth[abstract]]",
        ),
        (
            "eHealth[tiab] AND mHealth[tiab]",
            "AND[OR[eHealth[abstract], eHealth[title]], OR[mHealth[abstract], mHealth[title]]]",
        ),
        (
            "(eHealth[tiab] OR mHealth[tiab]) OR (diabetes[tiab] AND digital[tiab])",
            "OR[OR[eHealth[title], mHealth[title], eHealth[abstract], mHealth[abstract]], AND[OR[diabetes[abstract], diabetes[title]], OR[digital[abstract], digital[title]]]]",
        ),
        (
            "eHealth[tiab] OR mHealth[ti]",
            "OR[OR[eHealth[abstract], eHealth[title]], mHealth[title]]",
        ),
        (
            "eHealth[tiab] OR mHealth[tiab]",
            "OR[eHealth[title], mHealth[title], eHealth[abstract], mHealth[abstract]]",
        ),
        (
            '"digital health"[ti:~2]',
            "OR[NEAR/2[digital[title], health[title]], NEAR/2[health[title], digital[title]]]",
        ),
        (
            'eHealth[ti] AND "digital health"[ti:~2]',
            "AND[eHealth[title], OR[NEAR/2[digital[title], health[title]], NEAR/2[health[title], digital[title]]]]",
        ),
        (
            '"digital health"[tiab:~2]',
            "OR[NEAR/2[digital[abstract], health[abstract]], NEAR/2[health[abstract], digital[abstract]], NEAR/2[digital[title], health[title]], NEAR/2[health[title], digital[title]]]",
        ),
        (
            '"digital health platforms"[tiab:~0]',
            "OR[NEAR/0[digital[abstract], health[abstract]], NEAR/0[digital[abstract], platforms[abstract]], NEAR/0[health[abstract], digital[abstract]], NEAR/0[health[abstract], platforms[abstract]], NEAR/0[platforms[abstract], digital[abstract]], NEAR/0[platforms[abstract], health[abstract]], NEAR/0[digital[title], health[title]], NEAR/0[digital[title], platforms[title]], NEAR/0[health[title], digital[title]], NEAR/0[health[title], platforms[title]], NEAR/0[platforms[title], digital[title]], NEAR/0[platforms[title], health[title]]]",
        ),
    ],
)
def test_translation_to_generic(query_str: str, expected_generic: str) -> None:
    print(query_str)
    parser = PubMedParser_v1(query_str)
    query = parser.parse()

    translator = PubMedTranslator_v1()
    generic = translator.to_generic_syntax(query)

    assert expected_generic == generic.to_generic_string(), print(
        generic.to_generic_string()
    )
