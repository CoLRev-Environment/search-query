#!/usr/bin/env python
"""Tests for PubMedParser_v1"""
import pytest

from search_query.constants import Colors
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import ListQuerySyntaxError
from search_query.exception import SearchQueryException
from search_query.parser import parse
from search_query.pubmed.linter import PubmedQueryStringLinter
from search_query.pubmed.v_1.parser import PubMedListParser_v1
from search_query.pubmed.v_1.parser import PubMedParser_v1

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
                    type=TokenTypes.TERM,
                    position=(1, 18),
                ),
                Token(value="[tw]", type=TokenTypes.FIELD, position=(19, 23)),
                Token(value="OR", type=TokenTypes.LOGIC_OPERATOR, position=(24, 26)),
                Token(
                    value='"remote monitoring"',
                    type=TokenTypes.TERM,
                    position=(26, 45),
                ),
                Token(value="[tw]", type=TokenTypes.FIELD, position=(45, 49)),
                Token(value=")", type=TokenTypes.PARENTHESIS_CLOSED, position=(49, 50)),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(50, 53)),
                Token(
                    value="wearable device",
                    type=TokenTypes.TERM,
                    position=(54, 69),
                ),
                Token(value="[tw]", type=TokenTypes.FIELD, position=(69, 73)),
                Token(value="NOT", type=TokenTypes.LOGIC_OPERATOR, position=(73, 76)),
                Token(value="Comment", type=TokenTypes.TERM, position=(77, 84)),
                Token(value="[pt]", type=TokenTypes.FIELD, position=(84, 88)),
            ],
        ),
        (
            "home care workers [Title] OR health care workers [Title]",
            [
                Token(
                    value="home care workers",
                    type=TokenTypes.TERM,
                    position=(0, 17),
                ),
                Token(value="[Title]", type=TokenTypes.FIELD, position=(18, 25)),
                Token(value="OR", type=TokenTypes.LOGIC_OPERATOR, position=(26, 28)),
                Token(
                    value="health care workers",
                    type=TokenTypes.TERM,
                    position=(29, 48),
                ),
                Token(value="[Title]", type=TokenTypes.FIELD, position=(49, 56)),
            ],
        ),
        (
            'technician*[ Title/Abstract] OR "Personnel"[ MeSH Terms]',
            [
                Token(value="technician*", type=TokenTypes.TERM, position=(0, 11)),
                Token(
                    value="[ Title/Abstract]", type=TokenTypes.FIELD, position=(11, 28)
                ),
                Token(value="OR", type=TokenTypes.LOGIC_OPERATOR, position=(29, 31)),
                Token(value='"Personnel"', type=TokenTypes.TERM, position=(32, 43)),
                Token(value="[ MeSH Terms]", type=TokenTypes.FIELD, position=(43, 56)),
            ],
        ),
    ],
)
def test_tokenization(query_str: str, expected_tokens: list) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = PubMedParser_v1(query_str)
    parser.tokenize()
    assert parser.tokens == expected_tokens, print(parser.tokens)


@pytest.mark.parametrize(
    "tokens, expected_codes, description",
    [
        (
            [
                Token("AND", TokenTypes.LOGIC_OPERATOR, (0, 3)),
                Token("cancer", TokenTypes.TERM, (4, 10)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Cannot start with LOGIC_OPERATOR",
        ),
        (
            [
                Token("cancer", TokenTypes.TERM, (0, 6)),
                Token("AND", TokenTypes.LOGIC_OPERATOR, (7, 10)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Cannot end with LOGIC_OPERATOR",
        ),
        (
            [
                Token("cancer", TokenTypes.TERM, (0, 6)),
                Token("treatment", TokenTypes.TERM, (7, 16)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            'Missing operator between "cancer treatment"',
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
                Token("(", TokenTypes.PARENTHESIS_OPEN, (0, 1)),
                Token("[tiab]", TokenTypes.FIELD, (1, 3)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Invalid search field position",
        ),
        (
            [
                Token(")", TokenTypes.PARENTHESIS_CLOSED, (0, 1)),
                Token("OR", TokenTypes.LOGIC_OPERATOR, (2, 4)),
                Token("termb", TokenTypes.TERM, (2, 4)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Cannot start with PARENTHESIS_CLOSED",
        ),
        (
            [
                Token("[ti]", TokenTypes.FIELD, (0, 2)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Cannot start with FIELD",
        ),
        (
            [
                Token("(", TokenTypes.PARENTHESIS_OPEN, (0, 1)),
                Token("AND", TokenTypes.LOGIC_OPERATOR, (1, 4)),
                Token("diabetes", TokenTypes.TERM, (5, 13)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Invalid operator position",
        ),
        (
            [
                Token("diabetes", TokenTypes.TERM, (0, 10)),
            ],
            [],
            "",
        ),
    ],
)
def test_pubmed_invalid_token_sequences(
    tokens: list, expected_codes: list, description: str
) -> None:
    print(tokens)
    linter = PubmedQueryStringLinter(query_str="")
    linter.tokens = tokens
    linter.check_invalid_token_sequences()

    actual_codes = [msg["label"] for msg in linter.messages]
    print(linter.messages)
    print(actual_codes)
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
    "query_str, field_general, messages",
    [
        (
            "(eHealth[Text Word]) Sort by: Publication Date",
            "",
            [
                {
                    "code": "PARSE_0009",
                    "label": "unsupported-suffix",
                    "message": "Unsupported suffix in search query",
                    "is_fatal": False,
                    "position": [(20, 46)],
                    "details": "Removed unsupported text at the end of the query.",
                }
            ],
        ),
        (
            "Pubmed with no restrictions: (eHealth[Text Word])",
            "",
            [
                {
                    "code": "PARSE_0010",
                    "label": "unsupported-prefix-platform-identifier",
                    "message": "Query starts with platform identifier",
                    "is_fatal": False,
                    "position": [],
                    "details": "Unsupported prefix '\x1b[91mPubmed with no restrictions: \x1b[0m' in query string. ",
                }
            ],
        ),
        (
            '("health tracking" OR "remote monitoring") AND (("mobile application" OR "wearable device")',
            "Title",
            [
                {
                    "code": "PARSE_0002",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(47, 48)],
                    "details": "Unbalanced opening parenthesis",
                },
            ],
        ),
        (
            '"eHealth[ti]',
            "",
            [
                {
                    "code": "PARSE_0003",
                    "label": "unbalanced-quotes",
                    "message": "Quotes are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(0, 8)],
                    "details": "Unmatched opening quote",
                }
            ],
        ),
        (
            'eHealth"[ti]',
            "",
            [
                {
                    "code": "PARSE_0003",
                    "label": "unbalanced-quotes",
                    "message": "Quotes are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(0, 8)],
                    "details": "Unmatched closing quote",
                }
            ],
        ),
        (
            'eHeal"th[ti]',
            "",
            [
                {
                    "code": "PARSE_0003",
                    "label": "unbalanced-quotes",
                    "message": "Quotes are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(0, 8)],
                    "details": "Unbalanced quotes inside term",
                }
            ],
        ),
        (
            'eHe"a"l"t"h[ti]',
            "",
            [
                {
                    "code": "PARSE_0003",
                    "label": "unbalanced-quotes",
                    "message": "Quotes are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(0, 11)],
                    "details": "Suspicious or excessive quote usage",
                }
            ],
        ),
        (
            '("health tracking" OR "remote monitoring")) AND ("mobile application" OR "wearable device")',
            "Title",
            [
                {
                    "code": "PARSE_0002",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(42, 43)],
                    "details": "Unbalanced closing parenthesis",
                },
            ],
        ),
        (
            '"health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")',
            "Title",
            [
                {
                    "code": "STRUCT_0001",
                    "label": "implicit-precedence",
                    "message": "Operator changed at the same level (explicit parentheses are recommended)",
                    "is_fatal": False,
                    "position": [(18, 20), (49, 52)],
                    "details": "The query uses multiple operators, but without parentheses to make the\nintended logic explicit. PubMed evaluates queries strictly from left to\nright without applying traditional operator precedence. This can lead to\nunexpected interpretations of the query.\n\nSpecifically:\n- \x1b[93mOR\x1b[0m is evaluated first because it is the leftmost operator\n- \x1b[93mAND\x1b[0m is evaluated last because it is the rightmost operator\n\nTo fix this, search-query adds artificial parentheses around\noperators based on their left-to-right position in the query.\n\n",
                },
                {
                    "code": "FIELD_0003",
                    "label": "field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "The search field is extracted and should be included in the query.",
                },
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [(0, 17), (22, 30), (35, 47), (54, 74), (78, 95)],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                },
            ],
        ),
        # Note: corresponds to the search for "Industry 4 0" (replaced dot with space)
        (
            '"healthcare" AND "Industry 4.0"',
            "Title",
            [
                {
                    "code": "FIELD_0003",
                    "label": "field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "The search field is extracted and should be included in the query.",
                },
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [(0, 12), (17, 31)],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                },
                {
                    "code": "PUBMED_0002",
                    "label": "character-replacement",
                    "message": "Character replacement",
                    "is_fatal": False,
                    "position": [(28, 29)],
                    "details": "Character '.' in search term will be replaced with whitespace.\nSee PubMed character conversions: https://pubmed.ncbi.nlm.nih.gov/help/)",
                },
            ],
        ),
        (
            '"health tracking" AND AI*',
            "Title",
            [
                {
                    "code": "FIELD_0003",
                    "label": "field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "The search field is extracted and should be included in the query.",
                },
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [(0, 17), (22, 25)],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                },
                {
                    "code": "PUBMED_0003",
                    "label": "invalid-wildcard-use",
                    "message": "Invalid use of the wildcard operator *",
                    "is_fatal": False,
                    "position": [(22, 25)],
                    "details": "Wildcards cannot be used for short strings (shorter than 4 characters).",
                },
            ],
        ),
        (
            '("eHealth" OR "digital health")[tiab]',
            "",
            [
                {
                    "code": "PARSE_0004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(30, 37)],
                    "details": "Nested queries cannot have search fields",
                },
            ],
        ),
        (
            '"eHealth"[tiab] "digital health"[tiab]',
            "Title",
            [
                {
                    "code": "PARSE_0004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(9, 32)],
                    "details": 'Missing operator between "[tiab] "digital health""',
                },
            ],
        ),
        (
            '("health tracking" OR "remote monitoring")("mobile application" OR "wearable device")',
            "Title",
            [
                {
                    "code": "PARSE_0004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(41, 43)],
                    "details": 'Missing operator between ") ("',
                },
            ],
        ),
        (
            "digital health[tiab:~5]",
            "",
            [
                {
                    "code": "STRUCT_0004",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(0, 14)],
                    "details": "Proximity search requires 2 or more search terms enclosed in double quotes.",
                },
            ],
        ),
        (
            '"digital health"[tiab:~0.5]',
            "",
            [
                {
                    "code": "STRUCT_0004",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(16, 27)],
                    "details": "Proximity value '0.5' is not a digit. Using default 3 instead.",
                },
            ],
        ),
        (
            '"digital health"[tiab:~5] OR "eHealth"[tiab:~5]',
            "",
            [
                {
                    "code": "STRUCT_0004",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(29, 38)],
                    "details": "Proximity search requires 2 or more search terms enclosed in double quotes.",
                },
            ],
        ),
        (
            '"digital health"[sb:~5] OR "mobile health"[sb:~5]',
            "",
            [
                {
                    "code": "STRUCT_0004",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(16, 23)],
                    "details": "Proximity operator is not supported: '[sb:~5]' (supported search fields: [tiab], [ti], [ad])",
                },
                {
                    "code": "STRUCT_0004",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(42, 49)],
                    "details": "Proximity operator is not supported: '[sb:~5]' (supported search fields: [tiab], [ti], [ad])",
                },
            ],
        ),
        (
            '("remote monitoring" NOT "in-person") AND "health outcomes"',
            "Title",
            [
                {
                    "code": "FIELD_0003",
                    "label": "field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "The search field is extracted and should be included in the query.",
                },
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [(1, 20), (25, 36), (42, 59)],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                },
            ],
        ),
        (
            '"device" AND ("wearable device" AND "health tracking")',
            "Title",
            [
                {
                    "code": "FIELD_0003",
                    "label": "field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "The search field is extracted and should be included in the query.",
                },
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [(0, 8), (14, 31), (36, 53)],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                },
                {
                    "code": "QUALITY_0004",
                    "label": "unnecessary-parentheses",
                    "message": "Unnecessary parentheses in queries",
                    "is_fatal": False,
                    "position": [],
                    "details": 'Unnecessary parentheses around AND block(s). A query with the structure\nA AND \x1b[91m(\x1b[0mB AND C\x1b[91m)\x1b[0m\n can be simplified to \nA AND B AND C\nwith\n  A: "device"\n  B: "wearable device"\n  C: "health tracking".\n',
                },
                {
                    "code": "QUALITY_0005",
                    "label": "redundant-term",
                    "message": "Redundant term in the query",
                    "is_fatal": False,
                    "position": [(0, 8), (14, 31)],
                    "details": 'The term \x1b[93m"wearable device"\x1b[0m is more specific than \x1b[93m"device"\x1b[0m—results matching \x1b[93m"wearable device"\x1b[0m are a subset of those matching \x1b[93m"device"\x1b[0m.\nSince both are connected with AND, including \x1b[93m"device"\x1b[0m does not further restrict the result set and is therefore redundant.',
                },
            ],
        ),
        (
            '("device"[ti] OR ("mobile application"[ti] OR "wearable device"[ti])) AND "health tracking"[ti]',
            "",
            [
                {
                    "code": "QUALITY_0004",
                    "label": "unnecessary-parentheses",
                    "message": "Unnecessary parentheses in queries",
                    "is_fatal": False,
                    "position": [],
                    "details": 'Unnecessary parentheses around AND block(s). A query with the structure\n(A OR \x1b[91m(\x1b[0mB OR C)\x1b[91m)\x1b[0m AND D\n can be simplified to \n(A OR B OR C) AND D\nwith\n  A: "device"\n  B: "mobile application"\n  C: "wearable device"\n  D: "health tracking".\n',
                },
                {
                    "code": "QUALITY_0005",
                    "label": "redundant-term",
                    "message": "Redundant term in the query",
                    "is_fatal": False,
                    "position": [(1, 9), (46, 63)],
                    "details": 'Results for term \x1b[93m"wearable device"\x1b[0m are contained in the more general search for \x1b[93m"device"\x1b[0m.\nAs both terms are connected with OR, the term "wearable device" is redundant.',
                },
            ],
        ),
        (
            '"eHealth"[ab]',
            "",
            [
                {
                    "code": "FIELD_0001",
                    "label": "field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": [(9, 13)],
                    "details": "Search field [ab] is not supported.",
                }
            ],
        ),
        # (
        #     '(("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) AND 2019/01/01:2019/12/01[publication date]) OR ("ehealth"[Title/Abstract])',
        #     "",
        #     [
        #         {
        #             "code": "QUALITY_0002",
        #             "label": "date-filter-in-subquery",
        #             "message": "Date filter in subquery",
        #             "is_fatal": False,
        #             "position": [(70, 91), (91, 109)],
        #             "details": "Check whether date filters should apply to the entire query.",
        #         }
        #     ],
        # ),
        (
            'TI="eHealth"',
            "",
            [
                {
                    "code": "PARSE_0006",
                    "label": "invalid-syntax",
                    "message": "Query contains invalid syntax",
                    "is_fatal": True,
                    "position": [(0, 3)],
                    "details": "PubMed fields must be enclosed in brackets and after a search term, e.g. robot[TIAB] or monitor[TI]. 'TI=' is invalid.",
                },
            ],
        ),
        (
            "(eHealth OR mHealth)[tiab]",
            "",
            [
                {
                    "code": "PARSE_0004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(19, 26)],
                    "details": "Nested queries cannot have search fields",
                },
            ],
        ),
        (
            "device[ti] OR (wearable[ti] AND 2000:2010[dp])",
            "",
            [
                {
                    "code": "QUALITY_0002",
                    "label": "date-filter-in-subquery",
                    "message": "Date filter in subquery",
                    "is_fatal": False,
                    "position": [(32, 41), (41, 45)],
                    "details": "Check whether date filters should apply to the entire query.",
                }
            ],
        ),
        (
            '"activity"[Title/Abstract] AND ("cancer"[Title/Abstract] OR "Lancet"[Journal])',
            "",
            [
                {
                    "code": "QUALITY_0003",
                    "label": "journal-filter-in-subquery",
                    "message": "Journal (or publication name) filter in subquery",
                    "is_fatal": False,
                    "position": [(60, 68)],
                    "details": "Check whether journal/publication-name filters ([Journal]) should apply to the entire query.",
                }
            ],
        ),
        (
            '("Sleep"[mh] OR "Sleep Deprivation"[mh]) AND "vigilant attention"[ti]',
            "",
            [
                {
                    "code": "QUALITY_0005",
                    "label": "redundant-term",
                    "message": "Redundant term in the query",
                    "is_fatal": False,
                    "position": [(1, 8), (16, 35)],
                    "details": 'Results for term \x1b[93m"Sleep Deprivation"\x1b[0m are contained in the more general search for \x1b[93m"Sleep"\x1b[0m.\nAs both terms are connected with OR, the term "Sleep Deprivation" is redundant.',
                }
            ],
        ),
        (
            '("Sleep"[mh] AND "Sleep Deprivation"[mh]) AND "vigilant attention"[ti]',
            "",
            [
                {
                    "code": "QUALITY_0004",
                    "label": "unnecessary-parentheses",
                    "message": "Unnecessary parentheses in queries",
                    "is_fatal": False,
                    "position": [],
                    "details": 'Unnecessary parentheses around AND block(s). A query with the structure\n\x1b[91m(\x1b[0mA AND B\x1b[91m)\x1b[0m AND C\n can be simplified to \nA AND B AND C\nwith\n  A: "Sleep"\n  B: "Sleep Deprivation"\n  C: "vigilant attention".\n',
                },
                {
                    "code": "QUALITY_0005",
                    "label": "redundant-term",
                    "message": "Redundant term in the query",
                    "is_fatal": False,
                    "position": [(1, 8), (17, 36)],
                    "details": 'The term \x1b[93m"Sleep Deprivation"\x1b[0m is more specific than \x1b[93m"Sleep"\x1b[0m—results matching \x1b[93m"Sleep Deprivation"\x1b[0m are a subset of those matching \x1b[93m"Sleep"\x1b[0m.\nSince both are connected with AND, including \x1b[93m"Sleep"\x1b[0m does not further restrict the result set and is therefore redundant.',
                },
            ],
        ),
        (
            '"Pickwickian Syndrome*"[tiab] OR "Pickwickian Syndrome*"[tiab]',
            "",
            [
                {
                    "code": "QUALITY_0005",
                    "label": "redundant-term",
                    "message": "Redundant term in the query",
                    "is_fatal": False,
                    "position": [(0, 23), (33, 56)],
                    "details": 'Term "Pickwickian Syndrome*" is contained multiple times i.e., redundantly.',
                }
            ],
        ),
        (
            '((AI OR "Artificial Intelligence") AND Aversion) OR ((AI OR "Artificial Intelligence") AND Appreciation)',
            "",
            [
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [
                        (2, 4),
                        (8, 33),
                        (39, 47),
                        (54, 56),
                        (60, 85),
                        (91, 103),
                    ],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                },
                {
                    "code": "QUALITY_0001",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(39, 47), (91, 103)],
                    "details": 'The queries share \x1b[90midentical query parts\x1b[0m:\n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND \x1b[93mAversion[all]\x1b[0m OR \n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND \x1b[93mAppreciation[all]\x1b[0m\nCombine the \x1b[93mdiffering parts\x1b[0m into a \x1b[92msingle OR-group\x1b[0m to reduce redundancy:\n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND (\x1b[92mAversion[all] OR Appreciation[all]\x1b[0m)',
                },
            ],
        ),
        (
            '(Algorithm* Aversion) OR (Algorithm* Appreciation) OR ((AI OR "Artificial Intelligence") AND Aversion) OR ((AI OR "Artificial Intelligence") AND Appreciation) OR ("AI recommendation" OR "Artificial intelligence recommendation" OR "Machine learning recommendation" OR "ML recommendation") OR ("AI decision*" OR "Artificial intelligence decision*" OR "Algorithm* decision" OR "Machine learning decision*" OR "ML decision*") OR ("AI Advice" OR "Artificial intelligence advice" OR "Algorithm* advice" OR "Machine learning advice" OR "ML advice") OR (("AI" OR "Artificial Intelligence" OR "Algorithm*" OR "Machine learning" OR "ML") AND "Decision aid")',
            "",
            [
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [
                        (1, 20),
                        (26, 49),
                        (56, 58),
                        (62, 87),
                        (93, 101),
                        (108, 110),
                        (114, 139),
                        (145, 157),
                        (163, 182),
                        (186, 226),
                        (230, 263),
                        (267, 286),
                        (292, 306),
                        (310, 345),
                        (349, 370),
                        (374, 402),
                        (406, 420),
                        (426, 437),
                        (441, 473),
                        (477, 496),
                        (500, 525),
                        (529, 540),
                        (547, 551),
                        (555, 580),
                        (584, 596),
                        (600, 618),
                        (622, 626),
                        (632, 646),
                    ],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                },
                {
                    "code": "QUALITY_0004",
                    "label": "unnecessary-parentheses",
                    "message": "Unnecessary parentheses in queries",
                    "is_fatal": False,
                    "position": [],
                    "details": 'Unnecessary parentheses around OR block(s). A query with the structure\nA OR B OR ((C OR D) AND E) OR ((F OR G) AND H) OR \x1b[91m(\x1b[0mI OR ...\x1b[91m)\x1b[0m OR \x1b[91m(\x1b[0mJ OR ...\x1b[91m)\x1b[0m OR \x1b[91m(\x1b[0mK OR ...\x1b[91m)\x1b[0m OR ((L OR ...) AND M)\n can be simplified to \nA OR B OR ((C OR D) AND E) OR ((F OR G) AND H) OR I OR ... OR J OR ... OR K OR ... OR ((L OR ...) AND M)\nwith\n  A: Algorithm* Aversion\n  B: Algorithm* Appreciation\n  C: AI\n  D: "Artificial Intelligence"\n  E: Aversion\n  F: AI\n  G: "Artificial Intelligence"\n  H: Appreciation\n  I: "AI recommendation"\n  J: "AI decision*"\n  K: "AI Advice"\n  L: "AI"\n  M: "Decision aid".\n',
                },
                {
                    "code": "QUALITY_0001",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(93, 101), (145, 157)],
                    "details": 'The queries share \x1b[90midentical query parts\x1b[0m:\n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND \x1b[93mAversion[all]\x1b[0m OR \n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND \x1b[93mAppreciation[all]\x1b[0m\nCombine the \x1b[93mdiffering parts\x1b[0m into a \x1b[92msingle OR-group\x1b[0m to reduce redundancy:\n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND (\x1b[92mAversion[all] OR Appreciation[all]\x1b[0m)',
                },
                {
                    "code": "QUALITY_0001",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(93, 101), (632, 646)],
                    "details": 'The queries share \x1b[90midentical query parts\x1b[0m:\n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND \x1b[93mAversion[all]\x1b[0m OR \n(\x1b[90m"AI"[all] OR "Artificial Intelligence"[all] OR "Algorithm*"[all] OR "Machine learning"[all] OR "ML"[all]\x1b[0m) AND \x1b[93m"Decision aid"[all]\x1b[0m\nCombine the \x1b[93mdiffering parts\x1b[0m into a \x1b[92msingle OR-group\x1b[0m to reduce redundancy:\n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND (\x1b[92mAversion[all] OR "Decision aid"[all]\x1b[0m)',
                },
                {
                    "code": "QUALITY_0001",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(145, 157), (632, 646)],
                    "details": 'The queries share \x1b[90midentical query parts\x1b[0m:\n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND \x1b[93mAppreciation[all]\x1b[0m OR \n(\x1b[90m"AI"[all] OR "Artificial Intelligence"[all] OR "Algorithm*"[all] OR "Machine learning"[all] OR "ML"[all]\x1b[0m) AND \x1b[93m"Decision aid"[all]\x1b[0m\nCombine the \x1b[93mdiffering parts\x1b[0m into a \x1b[92msingle OR-group\x1b[0m to reduce redundancy:\n(\x1b[90mAI[all] OR "Artificial Intelligence"[all]\x1b[0m) AND (\x1b[92mAppreciation[all] OR "Decision aid"[all]\x1b[0m)',
                },
            ],
        ),
        (
            "eHealth[ti] | mHealth[ti]",
            "",
            [
                {
                    "code": "STRUCT_0003",
                    "label": "boolean-operator-readability",
                    "message": "Boolean operator readability",
                    "is_fatal": False,
                    "position": [(12, 13)],
                    "details": "Use AND, OR, NOT instead of |&",
                }
            ],
        ),
    ],
)
def test_linter(
    query_str: str,
    field_general: str,
    messages: list,
) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = PubMedParser_v1(query_str, field_general=field_general)
    try:
        parser.parse()
    except SearchQueryException:
        pass
    print(parser.linter.messages)
    assert messages == parser.linter.messages


@pytest.mark.parametrize(
    "query_str, field_general, messages",
    [
        (
            "eHealth[tiab]",
            "Title",
            [
                {
                    "code": "FIELD_0003",
                    "label": "field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "The search field is extracted and should be included in the query.",
                }
            ],
        ),
        (
            "eHealth[ti]",
            "Title",
            [
                {
                    "code": "FIELD_0003",
                    "label": "field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "The search field is extracted and should be included in the query.",
                }
            ],
        ),
        (
            "eHealth",
            "Title",
            [
                {
                    "code": "FIELD_0003",
                    "label": "field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": [],
                    "details": "The search field is extracted and should be included in the query.",
                },
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [(0, 7)],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                },
            ],
        ),
        (
            "eHealth",
            "",
            [
                {
                    "code": "FIELD_0004",
                    "label": "field-implicit",
                    "message": "Search field is implicitly specified",
                    "is_fatal": False,
                    "position": [(0, 7)],
                    "details": "The search field is implicit (will be set to [all] by PubMed).",
                }
            ],
        ),
        (
            "eHealth[tldr]",
            "",
            [
                {
                    "code": "FIELD_0001",
                    "label": "field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": [(7, 13)],
                    "details": "Search field [tldr] is not supported.",
                }
            ],
        ),
        (
            "(dHealth OR mHealth)[ti]",
            "",
            [
                {
                    "code": "PARSE_0004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(19, 24)],
                    "details": "Nested queries cannot have search fields",
                },
            ],
        ),
        (
            '"eHealth[ti] AND (activity[ti] OR tracking[ti])"',
            "",
            [
                {
                    "code": "PARSE_0007",
                    "label": "query-in-quotes",
                    "message": "The whole Search string is in quotes.",
                    "is_fatal": False,
                    "position": [],
                    "details": "",
                }
            ],
        ),
    ],
)
def test_linter_with_general_field(
    query_str: str,
    field_general: str,
    messages: list,
) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = PubMedParser_v1(query_str, field_general=field_general)
    try:
        parser.parse()
    except SearchQueryException:
        pass

    parser.print_tokens()
    print(parser.linter.messages)

    assert messages == parser.linter.messages


@pytest.mark.parametrize(
    "query_str, field_general, expected_parsed",
    [
        (
            '(eHealth[Title/Abstract] OR "eHealth"[MeSH Terms]) AND Review[Publication Type]',
            "",
            'AND[OR[eHealth[[Title/Abstract]], "eHealth"[[MeSH Terms]]], Review[[Publication Type]]]',
        ),
        # Artificial parentheses:
        (
            '"health tracking" OR "remote monitoring" AND "wearable device"',
            "All Fields",
            'AND[OR["health tracking"[[all]], "remote monitoring"[[all]]], "wearable device"[[all]]]',
        ),
        (
            '"AI" AND "robotics" OR "ethics"',
            "All Fields",
            'OR[AND["AI"[[all]], "robotics"[[all]]], "ethics"[[all]]]',
        ),
        (
            '"AI" OR "robotics" AND "ethics"',
            "All Fields",
            'AND[OR["AI"[[all]], "robotics"[[all]]], "ethics"[[all]]]',
        ),
        (
            '"AI" NOT "robotics" OR "ethics"',
            "All Fields",
            'OR[NOT["AI"[[all]], "robotics"[[all]]], "ethics"[[all]]]',
        ),
        (
            '"digital health" AND ("apps" OR "wearables" NOT "privacy") OR "ethics"',
            "All Fields",
            'OR[AND["digital health"[[all]], NOT[OR["apps"[[all]], "wearables"[[all]]], "privacy"[[all]]]], "ethics"[[all]]]',
        ),
        (
            '"eHealth" OR "digital health" AND "bias" NOT "equity" OR "policy"',
            "All Fields",
            'OR[NOT[AND[OR["eHealth"[[all]], "digital health"[[all]]], "bias"[[all]]], "equity"[[all]]], "policy"[[all]]]',
        ),
        (
            'eHealth[ti] AND ("2006/01/01"[Date - Create] : "2023/08/18"[Date - Create])',
            "",
            'AND[eHealth[[ti]], RANGE["2006/01/01"[[Date - Create]], "2023/08/18"[[Date - Create]]]]',
        ),
        (
            '("1995/01/01"[pdat] : "3000"[pdat])',
            "",
            'RANGE["1995/01/01"[[pdat]], "3000"[[pdat]]]',
        ),
        ('"wearable device"[ti:~2]', "", 'NEAR/2["wearable device"[[ti]]]'),
    ],
)
def test_parser(query_str: str, field_general: str, expected_parsed: str) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = PubMedParser_v1(query_str, field_general=field_general)
    query = parser.parse()

    assert expected_parsed == query.to_generic_string(), print(
        query.to_generic_string()
    )


def test_list_parser_case_1() -> None:
    query_list = """
1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] OR "Distributed leader*"[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. #1 OR #2
"""

    list_parser = PubMedListParser_v1(query_list=query_list)  #
    list_parser.parse()


def test_list_parser_case_2() -> None:
    query_list = """
1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] AND Distributed leader*[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. #1 AND #2 AND #4
"""
    list_parser = PubMedListParser_v1(query_list=query_list)
    try:
        list_parser.parse()
    except ListQuerySyntaxError:
        pass

    print(list_parser.linter.messages)
    assert list_parser.linter.messages == {
        "3": [
            {
                "code": "PARSE_1002",
                "label": "list-query-invalid-reference",
                "message": "Invalid list reference in list query",
                "is_fatal": True,
                "position": [(238, 240)],
                "details": "List reference #4 not found.",
            }
        ]
    }


def test_list_parser_case_3() -> None:
    query_list = """1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] AND Distributed leader*[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. #1 #2
"""
    print(query_list)

    list_parser = PubMedListParser_v1(query_list=query_list)
    try:
        list_parser.parse()
    except ListQuerySyntaxError:
        pass

    print(list_parser.linter.messages)
    assert list_parser.linter.messages == {
        -1: [],
        "1": [
            {
                "code": "PARSE_0004",
                "label": "invalid-token-sequence",
                "message": "The sequence of tokens is invalid.",
                "is_fatal": True,
                "position": [(106, 112)],
                "details": 'Missing operator between ") ("',
            },
            {
                "code": "STRUCT_0001",
                "label": "implicit-precedence",
                "message": "Operator changed at the same level (explicit parentheses are recommended)",
                "is_fatal": False,
                "position": [(33, 35), (67, 70)],
                "details": "The query uses multiple operators, but without parentheses to make the\nintended logic explicit. PubMed evaluates queries strictly from left to\nright without applying traditional operator precedence. This can lead to\nunexpected interpretations of the query.\n\nSpecifically:\n- \x1b[93mOR\x1b[0m is evaluated first because it is the leftmost operator\n- \x1b[93mAND\x1b[0m is evaluated last because it is the rightmost operator\n\nTo fix this, search-query adds artificial parentheses around\noperators based on their left-to-right position in the query.\n\n",
            },
        ],
    }


def test_general_list_parser_1() -> None:
    query_list = """
1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. #1 AND #2
"""

    list_parser = PubMedListParser_v1(query_list=query_list)
    list_parser.parse()

    print(list_parser.linter.messages)
    assert list_parser.linter.messages == {-1: []}


def test_general_list_parser_2() -> None:
    query_list = """
1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. (school[Title/Abstract] OR university[Title/Abstract])
4. #1 AND #2 OR #3
"""

    list_parser = PubMedListParser_v1(query_list=query_list)
    query = list_parser.parse()
    assert (
        query.to_string()
        == "((Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract]) AND (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])) OR (school[Title/Abstract] OR university[Title/Abstract])"
    )


def test_general_list_parser_3() -> None:
    query_list = """
1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] OR Distributed leader*[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. #1 AND #2
"""

    query = parse(query_list, platform=PLATFORM.PUBMED.value)

    assert (
        query.to_string()
        == "(Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] OR Distributed leader*[Title/Abstract]) AND (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])"
    )


def test_general_list_parser_4() -> None:
    query_list = """
1. Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] OR Distributed leader*[Title/Abstract]
2. acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract]
3. #1 AND #2
"""

    query = parse(query_list, platform=PLATFORM.PUBMED.value)

    assert (
        query.to_string()
        == "(Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] OR Distributed leader*[Title/Abstract]) AND (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])"
    )
