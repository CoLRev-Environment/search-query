#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.parser_base import QueryStringParser
from search_query.parser_pubmed import PubmedListParser
from search_query.parser_pubmed import PubmedParser
from search_query.query import Query

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, tokens",
    [
        (
            "fitbit[ti] AND (2000:2020[pdat])",
            [
                ("fitbit", (0, 6)),
                ("[ti]", (6, 10)),
                ("AND", (11, 14)),
                ("(", (15, 16)),
                ("2000:2020", (16, 25)),
                ("[pdat]", (25, 31)),
                (")", (31, 32)),
            ],
        ),
        (
            """"Tomography, X-Ray Computed"[Mesh]""",
            [('"Tomography, X-Ray Computed"', (0, 28)), ("[Mesh]", (28, 34))],
        ),
        (
            """fastfood*[tiab] OR fast foods[mj]""",
            [
                ("fastfood*", (0, 9)),
                ("[tiab]", (9, 15)),
                ("OR", (16, 18)),
                ("fast foods", (19, 29)),
                ("[mj]", (29, 33)),
            ],
        ),
        (
            """("demand generation"[Text Word]) OR "demand side" [Text Word] OR Implementation Science[MeSH Terms]""",
            [
                ("(", (0, 1)),
                ('"demand generation"', (1, 20)),
                ("[Text Word]", (20, 31)),
                (")", (31, 32)),
                ("OR", (33, 35)),
                ('"demand side"', (36, 49)),
                ("[Text Word]", (50, 61)),
                ("OR", (62, 64)),
                ("Implementation Science", (65, 87)),
                ("[MeSH Terms]", (87, 99)),
            ],
        ),
        (
            """"bile duct surg*"[Title/Abstract]""",
            [('"bile duct surg*"', (0, 17)), ("[Title/Abstract]", (17, 33))],
        ),
        (
            """"Healthier diet"[tiab:~5]""",
            [('"Healthier diet"', (0, 16)), ("[tiab:~5]", (16, 25))],
        ),
        (
            """Collab* or consort*""",
            [("Collab*", (0, 7)), ("or", (8, 10)), ("consort*", (11, 19))],
        ),
    ],
)
def test_tokenization_pubmed(query_string: str, tokens: tuple) -> None:
    print(query_string)
    print()
    pubmed_parser = PubmedParser(query_string)
    pubmed_parser.tokenize()
    print(pubmed_parser.tokens)
    print(pubmed_parser.get_token_types(pubmed_parser.tokens, legend=True))
    print(tokens)
    assert pubmed_parser.tokens == tokens


@pytest.mark.parametrize(
    "query_string, expected",
    [
        (
            """(Environment[Mesh:NoExp] OR "Environment health*"[tiab]) AND (Literacy[Mesh] OR Literac*[tiab])""",
            """AND[OR[Environment[mesh_no_exp], OR[Environment health*[ti], Environment health*[ab]]], OR[Literacy[mesh], OR[Literac*[ti], Literac*[ab]]]]""",
        ),
        (
            """"Environment health*"[tiab]""",
            """OR[Environment health*[ti], Environment health*[ab]]""",
        ),
        (
            """fitbit[ti] AND (2000:2020[pdat])""",
            """AND[fitbit[ti], 2000:2020[py]]""",
        ),
        ("""Collab* or consort*""", "OR[Collab*[all], consort*[all]]")
        # (
        #     """"Healthier diet"[tiab:~5]""",
        #     """""",
        # )
        # TODO : add "RANGE" operator
        # (
        #     """fitbit[ti] AND ("1995/01/01"[pdat] : "3000"[pdat])""",
        #     """"""
        # )
    ],
)
def test_pubmed_query_parser(query_string: str, expected: str) -> None:
    """Test the translation of a search query to a Pubmed query"""

    parser = PubmedParser(query_string)
    query = parser.parse()
    query_str = query.to_string()

    assert query_str == expected, print_debug(  # type: ignore
        parser, query, query_string, query_str
    )


@pytest.mark.parametrize(
    "query_string, expected",
    [
        (
            """1. "Caregivers"[Mesh] OR Caregiver[Title] OR caregivers[Title] OR carer[Title] OR carers[Title] OR care giver[Title] OR care givers[Title] OR caregiving [Title] OR care giving [Title]
2. "Continuity of Patient Care"[Mesh:NoExp] OR "Aftercare"[Mesh:NoExp] OR "Hospital to Home Transition"[Mesh] OR "Patient Discharge"[Mesh] OR "Retention in Care"[Mesh] OR "Transitional Care"[Mesh] OR Care continuity[Text Word] OR care continuum[Text Word] OR continuity of care[Text Word] OR discharge plan[Text Word] OR discharge plans[Text Word] OR discharge planning[Text Word] OR patient discharge[Text Word] OR hospital to home[Text Word] OR care transition[Text Word] OR care transitions[Text Word] OR after treatment[Text Word] OR follow up care[Text Word] OR follow up cares[Text Word] OR care retention[Text Word] OR home transition[Text Word] OR home transitions[Text Word] OR transitional care[Text Word]
3. dementia[Title] OR stroke[Title] OR alzheimers[Title] OR maternity[Title] OR emergency[Title] OR mental health[Title] OR suicide[Title] OR pediatric*[Title] OR child[Title] OR children[Title] OR infant*[Title] OR newborn*[Title] OR NICU[Title] OR asthma[Title] OR nursing home*[Title]OR "Dementia"[Mesh] OR "Stroke"[Mesh] OR "Hospice Care"[Mesh] OR "Nursing Homes"[Mesh] OR "Infant"[Mesh] OR "Intensive Care Units, Pediatric"[Mesh] OR "Maternal Health Services"[Mesh] OR "Pregnancy"[Mesh] OR "Oral Health"[Mesh] OR "Mental Health"[Mesh] OR "Mental Health Services"[Mesh] OR "Substance-Related Disorders"[Mesh] OR "Learning Disabilities"[Mesh] OR "Palliative Care"[Mesh] OR "Editorial" [Publication Type] OR "Letter" [Publication Type] OR "Comment" [Publication Type]
4. (#1 AND #2) NOT #3""",
            """"""
            """AND[AND[OR[Caregivers[mesh], Caregiver[ti], caregivers[ti], carer[ti], carers[ti], care giver[ti], care givers[ti], caregiving[ti], care giving[ti]], OR[Continuity of Patient Care[mesh_no_exp], Aftercare[mesh_no_exp], Hospital to Home Transition[mesh], Patient Discharge[mesh], Retention in Care[mesh], Transitional Care[mesh], Care continuity[tw], care continuum[tw], continuity of[tw], care[tw], discharge plan[tw], discharge plans[tw], discharge planning[tw], patient discharge[tw], hospital to[tw], home[tw], care transition[tw], care transitions[tw], after treatment[tw], follow up[tw], care[tw], follow up[tw], cares[tw], care retention[tw], home transition[tw], home transitions[tw], transitional care[tw]]], NOT[OR[dementia[ti], stroke[ti], alzheimers[ti], maternity[ti], emergency[ti], mental health[ti], suicide[ti], pediatric*[ti], child[ti], children[ti], infant*[ti], newborn*[ti], NICU[ti], asthma[ti], nursing home*[ti], Dementia[mesh], Stroke[mesh], Hospice Care[mesh], Nursing Homes[mesh], Infant[mesh], Intensive Care Units, Pediatric[mesh], Maternal Health Services[mesh], Pregnancy[mesh], Oral Health[mesh], Mental Health[mesh], Mental Health Services[mesh], Substance-Related Disorders[mesh], Learning Disabilities[mesh], Palliative Care[mesh], Editorial[pt], Letter[pt], Comment[pt]]]]""",
            # TODO : should be "...NOT #3"
        )
    ],
)
def test_pubmed_query_list_parser(query_string: str, expected: str) -> None:
    """Test the translation of a search query to a Pubmed query"""

    parser = PubmedListParser(query_string)
    query = parser.parse()
    query_str = query.to_string()

    assert query_str == expected, print_debug_list(  # type: ignore
        parser, query, query_string, query_str
    )


def print_debug(
    parser: QueryStringParser, query: Query, query_string: str, query_str: str
) -> None:
    print(query_string)
    print()
    # parser.parse_list()
    print()
    print(parser.get_token_types(parser.tokens))
    print(query_str)
    print(query.to_string("structured"))


def print_debug_list(
    parser: PubmedListParser, query: Query, query_string: str, query_str: str
) -> None:
    print(query_string)
    print()
    # parser.parse_list()
    print()
    # print(parser.get_token_types(parser.tokens))
    print(query_str)
    print(query.to_string("structured"))
