#!/usr/bin/env python
"""Tests for Pubmed search query parser."""
import pytest

from search_query.constants import Colors
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import ListQuerySyntaxError
from search_query.exception import QuerySyntaxError
from search_query.exception import SearchQueryException
from search_query.parser import parse
from search_query.pubmed.linter import PubmedQueryStringLinter
from search_query.pubmed.parser import PubmedListParser
from search_query.pubmed.parser import PubmedParser
from search_query.pubmed.translator import PubmedTranslator
from search_query.query_or import OrQuery
from search_query.query_term import Term

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
        ),
        (
            "home care workers [Title] OR health care workers [Title]",
            [
                Token(
                    value="home care workers",
                    type=TokenTypes.SEARCH_TERM,
                    position=(0, 17),
                ),
                Token(value="[Title]", type=TokenTypes.FIELD, position=(18, 25)),
                Token(value="OR", type=TokenTypes.LOGIC_OPERATOR, position=(26, 28)),
                Token(
                    value="health care workers",
                    type=TokenTypes.SEARCH_TERM,
                    position=(29, 48),
                ),
                Token(value="[Title]", type=TokenTypes.FIELD, position=(49, 56)),
            ],
        ),
        (
            'technician*[ Title/Abstract] OR "Personnel"[ MeSH Terms]',
            [
                Token(
                    value="technician*", type=TokenTypes.SEARCH_TERM, position=(0, 11)
                ),
                Token(
                    value="[ Title/Abstract]", type=TokenTypes.FIELD, position=(11, 28)
                ),
                Token(value="OR", type=TokenTypes.LOGIC_OPERATOR, position=(29, 31)),
                Token(
                    value='"Personnel"', type=TokenTypes.SEARCH_TERM, position=(32, 43)
                ),
                Token(value="[ MeSH Terms]", type=TokenTypes.FIELD, position=(43, 56)),
            ],
        ),
    ],
)
def test_tokenization(query_str: str, expected_tokens: list) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = PubmedParser(query_str, "")
    parser.tokenize()
    assert parser.tokens == expected_tokens, print(parser.tokens)


@pytest.mark.parametrize(
    "tokens, expected_codes, description",
    [
        (
            [
                Token("AND", TokenTypes.LOGIC_OPERATOR, (0, 3)),
                Token("cancer", TokenTypes.SEARCH_TERM, (4, 10)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Cannot start with LOGIC_OPERATOR",
        ),
        (
            [
                Token("cancer", TokenTypes.SEARCH_TERM, (0, 6)),
                Token("AND", TokenTypes.LOGIC_OPERATOR, (7, 10)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Cannot end with LOGIC_OPERATOR",
        ),
        (
            [
                Token("cancer", TokenTypes.SEARCH_TERM, (0, 6)),
                Token("treatment", TokenTypes.SEARCH_TERM, (7, 16)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Missing operator",
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
                Token("termb", TokenTypes.SEARCH_TERM, (2, 4)),
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
                Token("diabetes", TokenTypes.SEARCH_TERM, (5, 13)),
            ],
            [QueryErrorCode.INVALID_TOKEN_SEQUENCE.label],
            "Invalid operator position",
        ),
        (
            [
                Token("diabetes", TokenTypes.SEARCH_TERM, (0, 10)),
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
    "query_str, search_field_general, messages",
    [
        (
            '("health tracking" OR "remote monitoring") AND (("mobile application" OR "wearable device")',
            "Title",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(47, 48)],
                    "details": "Unbalanced opening parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                },
            ],
        ),
        (
            '"eHealth[ti]',
            "",
            [
                {
                    "code": "F1002",
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
                    "code": "F1002",
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
                    "code": "F1002",
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
                    "code": "F1002",
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
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(42, 43)],
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                },
            ],
        ),
        (
            '"health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")',
            "Title",
            [
                {
                    "code": "W0007",
                    "label": "implicit-precedence",
                    "message": "Operator changed at the same level (explicit parentheses are recommended)",
                    "is_fatal": False,
                    "position": [(18, 20)],
                    "details": "",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                },
            ],
        ),
        # Note: corresponds to the search for "Industry 4 0" (replaced dot with space)
        (
            '"healthcare" AND "Industry 4.0"',
            "Title",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                },
                {
                    "code": "W0010",
                    "label": "character-replacement",
                    "message": "Character replacement",
                    "is_fatal": False,
                    "position": [(28, 29)],
                    "details": "Character '.' in search term will be replaced with whitespace (see PubMed character conversions in https://pubmed.ncbi.nlm.nih.gov/help/)",
                },
            ],
        ),
        (
            '"health tracking" AND AI*',
            "Title",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                },
                {
                    "code": "E0006",
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
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(31, 37)],
                    "details": "Nested queries cannot have search fields",
                }
            ],
        ),
        (
            '"eHealth"[tiab] "digital health"[tiab]',
            "Title",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(9, 32)],
                    "details": "Missing operator",
                },
                {
                    "code": "E0002",
                    "label": "search-field-contradiction",
                    "message": "Contradictory search fields specified",
                    "is_fatal": False,
                    "position": [(9, 15)],
                    "details": "The search_field_general (Title) and the search_field [tiab] do not match.",
                },
                {
                    "code": "E0002",
                    "label": "search-field-contradiction",
                    "message": "Contradictory search fields specified",
                    "is_fatal": False,
                    "position": [(32, 38)],
                    "details": "The search_field_general (Title) and the search_field [tiab] do not match.",
                },
            ],
        ),
        (
            '("health tracking" OR "remote monitoring")("mobile application" OR "wearable device")',
            "Title",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(41, 43)],
                    "details": "Missing operator",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                },
            ],
        ),
        (
            "digital health[tiab:~5]",
            "",
            [
                {
                    "code": "E0005",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(0, 14)],
                    "details": "When using proximity operators, search terms consisting of 2 or more words (i.e., digital health) must be enclosed in double quotes",
                },
            ],
        ),
        (
            '"digital health"[tiab:~0.5]',
            "",
            [
                {
                    "code": "E0005",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(16, 27)],
                    "details": "Proximity value '0.5' is not a digit",
                },
            ],
        ),
        (
            '"digital health"[tiab:~5] OR "eHealth"[tiab:~5]',
            "",
            [],
        ),
        (
            '"digital health"[sb:~5] OR "eHealth"[sb:~5]',
            "",
            [
                {
                    "code": "E0005",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(16, 23)],
                    "details": "Proximity operator is not supported: '[sb:~5]' (supported search fields: [tiab], [ti], [ad])",
                },
                {
                    "code": "E0005",
                    "label": "invalid-proximity-use",
                    "message": "Invalid use of the proximity operator",
                    "is_fatal": False,
                    "position": [(36, 43)],
                    "details": "Proximity operator is not supported: '[sb:~5]' (supported search fields: [tiab], [ti], [ad])",
                },
            ],
        ),
        (
            '("remote monitoring" NOT "in-person") AND "health outcomes"',
            "Title",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                }
            ],
        ),
        (
            '"device" AND ("wearable device" AND "health tracking")',
            "Title",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                },
                {
                    "code": "W0004",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(0, 8), (14, 31)],
                    "details": 'The term "wearable device" is more specific than "device"—results matching "wearable device" are a subset of those matching "device". Since both are connected with AND, including "device" does not further restrict the result set and is therefore redundant.',
                },
            ],
        ),
        (
            '("device"[ti] OR ("mobile application"[ti] OR "wearable device"[ti])) AND "health tracking"[ti]',
            "",
            [
                {
                    "code": "W0004",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(1, 9), (46, 63)],
                    "details": 'Results for term "wearable device" are contained in the more general search for "device" (both terms are connected with OR). Therefore, the term "wearable device" is redundant.',
                }
            ],
        ),
        (
            '"eHealth"[ab]',
            "",
            [
                {
                    "code": "F2011",
                    "label": "search-field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": [(9, 13)],
                    "details": "Search field [ab] at position (9, 13) is not supported.",
                }
            ],
        ),
        (
            # '(("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) AND ("2020/01/01"[Date - Publication] : "2022/12/31"[Date - Publication])) OR ("ehealth"[Title/Abstract])',
            '(("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) AND 2019/01/01:2019/12/01[publication date]) OR ("ehealth"[Title/Abstract])',
            "",
            [
                {
                    "code": "W0011",
                    "label": "date-filter-in-subquery",
                    "message": "Date filter in subquery",
                    "is_fatal": False,
                    "position": [(70, 91)],
                    "details": "Please double-check whether date filters should apply to the entire query.",
                }
            ],
        ),
        (
            'TI="eHealth"',
            "",
            [
                {
                    "code": "F1010",
                    "label": "invalid-syntax",
                    "message": "Query contains invalid syntax",
                    "is_fatal": True,
                    "position": [(0, 3)],
                    "details": "PubMed fields must be enclosed in brackets and after a search term, e.g. robot[TIAB] or monitor[TI]. 'TI=' is invalid.",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search field is missing (TODO: default?)",
                },
            ],
        ),
        (
            "(eHealth OR mHealth)[tiab]",
            "",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(20, 26)],
                    "details": "Nested queries cannot have search fields",
                }
            ],
        ),
        (
            "device[ti] OR (wearable[ti] AND 2000:2010[dp])",
            "",
            [
                {
                    "code": "W0011",
                    "label": "date-filter-in-subquery",
                    "message": "Date filter in subquery",
                    "is_fatal": False,
                    "position": [(32, 41)],
                    "details": "Please double-check whether date filters should apply to the entire query.",
                }
            ],
        ),
        (
            '"activity"[Title/Abstract] AND ("cancer"[Title/Abstract] AND "Lancet"[Journal])',
            "",
            [
                {
                    "code": "W0014",
                    "label": "journal-filter-in-subquery",
                    "message": "Journal (or publication name) filter in subquery",
                    "is_fatal": False,
                    "position": [(61, 69)],
                    "details": "Please double-check whether journal/publication-name filters ([Journal]) should apply to the entire query.",
                }
            ],
        ),
        (
            '("Sleep"[mh] OR "Sleep Deprivation"[mh]) AND "vigilant attention"[ti]',
            "",
            [
                {
                    "code": "W0004",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(1, 8), (16, 35)],
                    "details": 'Results for term "Sleep Deprivation" are contained in the more general search for "Sleep" (both terms are connected with OR). Therefore, the term "Sleep Deprivation" is redundant.',
                }
            ],
        ),
        (
            '("Sleep"[mh] AND "Sleep Deprivation"[mh]) AND "vigilant attention"[ti]',
            "",
            [
                {
                    "code": "W0004",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(1, 8), (17, 36)],
                    "details": 'The term "Sleep Deprivation" is more specific than "Sleep"—results matching "Sleep Deprivation" are a subset of those matching "Sleep". Since both are connected with AND, including "Sleep" does not further restrict the result set and is therefore redundant.',
                }
            ],
        ),
        (
            '"Pickwickian Syndrome*"[tiab] OR "Pickwickian Syndrome*"[tiab]',
            "",
            [
                {
                    "code": "W0004",
                    "label": "query-structure-unnecessarily-complex",
                    "message": "Query structure is more complex than necessary",
                    "is_fatal": False,
                    "position": [(0, 23), (33, 56)],
                    "details": 'Term "Pickwickian Syndrome*" is contained multiple times i.e., redundantly.',
                }
            ],
        ),
    ],
)
def test_linter(
    query_str: str,
    search_field_general: str,
    messages: list,
) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = PubmedParser(query_str, search_field_general=search_field_general)
    try:
        parser.parse()
    except SearchQueryException:
        pass
    parser.print_tokens()
    print(parser.linter.messages)
    assert messages == parser.linter.messages


@pytest.mark.parametrize(
    "query_str, search_field_general, messages",
    [
        (
            "eHealth[tiab]",
            "Title",
            [
                {
                    "code": "E0002",
                    "label": "search-field-contradiction",
                    "message": "Contradictory search fields specified",
                    "is_fatal": False,
                    "position": [(7, 13)],
                    "details": "The search_field_general (Title) and the search_field [tiab] do not match.",
                }
            ],
        ),
        (
            "eHealth[ti]",
            "Title",
            [
                {
                    "code": "W0001",
                    "label": "search-field-redundant",
                    "message": "Recommend specifying search field only once in the search string",
                    "is_fatal": False,
                    "position": [(7, 11)],
                    "details": "The search_field_general (Title) and the search_field [ti] are redundant.",
                }
            ],
        ),
        (
            "eHealth",
            "Title",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search fields should be specified in the query instead of the search_field_general",
                }
            ],
        ),
        (
            "eHealth",
            "",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "Search field is missing (TODO: default?)",
                }
            ],
        ),
        (
            "eHealth[tldr]",
            "",
            [
                {
                    "code": "F2011",
                    "label": "search-field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": [(7, 13)],
                    "details": "Search field [tldr] at position (7, 13) is not supported.",
                }
            ],
        ),
        (
            "(hHealth OR mHealth)[ti]",
            "",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(20, 24)],
                    "details": "Nested queries cannot have search fields",
                }
            ],
        ),
    ],
)
def test_linter_with_general_search_field(
    query_str: str,
    search_field_general: str,
    messages: list,
) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = PubmedParser(query_str, search_field_general=search_field_general)
    try:
        parser.parse()
    except SearchQueryException:
        pass

    parser.print_tokens()
    print(parser.linter.messages)

    assert messages == parser.linter.messages


@pytest.mark.parametrize(
    "query_str, search_field_general, expected_parsed",
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
            'OR["health tracking"[[all]], AND["remote monitoring"[[all]], "wearable device"[[all]]]]',
        ),
        (
            '"AI" AND "robotics" OR "ethics"',
            "All Fields",
            'OR[AND["AI"[[all]], "robotics"[[all]]], "ethics"[[all]]]',
        ),
        (
            '"AI" OR "robotics" AND "ethics"',
            "All Fields",
            'OR["AI"[[all]], AND["robotics"[[all]], "ethics"[[all]]]]',
        ),
        (
            '"AI" NOT "robotics" OR "ethics"',
            "All Fields",
            'OR[NOT["AI"[[all]], "robotics"[[all]]], "ethics"[[all]]]',
        ),
        (
            '"digital health" AND ("apps" OR "wearables" NOT "privacy") OR "ethics"',
            "All Fields",
            'OR[AND["digital health"[[all]], OR["apps"[[all]], NOT["wearables"[[all]], "privacy"[[all]]]]], "ethics"[[all]]]',
        ),
        (
            '"eHealth" OR "digital health" AND "bias" NOT "equity" OR "policy"',
            "All Fields",
            'OR["eHealth"[[all]], AND["digital health"[[all]], NOT["bias"[[all]], "equity"[[all]]]], "policy"[[all]]]',
        ),
    ],
)
def test_parser(
    query_str: str, search_field_general: str, expected_parsed: str
) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = PubmedParser(query_str, search_field_general=search_field_general)
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

    list_parser = PubmedListParser(
        query_list=query_list  # , search_field_general="", mode=""
    )
    list_parser.parse()


def test_list_parser_case_2() -> None:
    query_list = """
1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] AND Distributed leader*[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. #1 AND #2 AND #4
"""

    list_parser = PubmedListParser(
        query_list=query_list, search_field_general="", mode=""
    )
    try:
        list_parser.parse()
    except ListQuerySyntaxError:
        pass

    print(list_parser.linter.messages)
    assert list_parser.linter.messages == {
        "3": [
            {
                "code": "F3003",
                "label": "invalid-list-reference",
                "message": "Invalid list reference in list query (not found)",
                "is_fatal": True,
                "position": [(14, 16)],
                "details": "List reference '#4' is invalid (a corresponding list element does not exist).",
            }
        ]
    }


def test_list_parser_case_3() -> None:
    query_list = """
1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] AND Distributed leader*[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. #1 #2
"""

    list_parser = PubmedListParser(
        query_list=query_list, search_field_general="", mode=""
    )
    try:
        list_parser.parse()
    except ListQuerySyntaxError:
        pass

    print(list_parser.linter.messages)
    assert list_parser.linter.messages == {
        "3": [
            {
                "code": "F1004",
                "label": "invalid-token-sequence",
                "message": "The sequence of tokens is invalid.",
                "is_fatal": True,
                "position": [(0, 5)],
                "details": "Two list references in a row",
            }
        ]
    }


@pytest.mark.parametrize(
    "query_str, expected_generic",
    [
        (
            "eHealth[ti]",
            "eHealth[ti]",
        ),
        (
            "eHealth[tiab] OR mHealth[tiab]",
            "OR[eHealth[ti], mHealth[ti], eHealth[ab], mHealth[ab]]",
        ),
        (
            "eHealth[tiab] AND mHealth[tiab]",
            "AND[OR[eHealth[ab], eHealth[ti]], OR[mHealth[ab], mHealth[ti]]]",
        ),
        (
            "eHealth[tiab] AND mHealth[tiab]",
            "AND[OR[eHealth[ab], eHealth[ti]], OR[mHealth[ab], mHealth[ti]]]",
        ),
        (
            "(eHealth[tiab] OR mHealth[tiab]) OR (diabetes[tiab] AND digital[tiab])",
            "OR[OR[eHealth[ti], mHealth[ti], eHealth[ab], mHealth[ab]], AND[OR[diabetes[ab], diabetes[ti]], OR[digital[ab], digital[ti]]]]",
        ),
        (
            "eHealth[tiab] OR mHealth[ti]",
            "OR[OR[eHealth[ab], eHealth[ti]], mHealth[ti]]",
        ),
        (
            "eHealth[tiab] OR mHealth[tiab]",
            "OR[eHealth[ti], mHealth[ti], eHealth[ab], mHealth[ab]]",
        ),
    ],
)
def test_translation_to_generic(query_str: str, expected_generic: str) -> None:
    print(query_str)
    parser = PubmedParser(query_str, "")
    query = parser.parse()

    translator = PubmedTranslator()
    generic = translator.to_generic_syntax(query)

    assert expected_generic == generic.to_generic_string(), print(
        generic.to_generic_string()
    )


def test_nested_query_with_field() -> None:
    try:
        OrQuery(
            [
                Term("health tracking"),
                Term("remote monitoring"),
            ],
            search_field="[tiab]",
            platform=PLATFORM.PUBMED.value,
        )
    except QuerySyntaxError as exc:
        assert exc.linter.messages == [
            {
                "code": "F2013",
                "label": "nested-query-with-search-field",
                "message": "A Nested query cannot have a search field.",
                "is_fatal": True,
                "position": [(-1, -1)],
                "details": "Nested query (operator) with search field is not supported",
            }
        ]


def test_general_list_parser_call() -> None:
    query_list = """
1. (Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] OR Distributed leader*[Title/Abstract])
2. (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract])
3. #1 AND #2
"""

    query = parse(query_list, platform=PLATFORM.PUBMED.value)

    assert (
        query.to_string()
        == "((Peer leader*[Title/Abstract] OR Shared leader*[Title/Abstract] OR Distributed leader*[Title/Abstract]) AND (acrobatics[Title/Abstract] OR aikido[Title/Abstract] OR archer[Title/Abstract] OR athletics[Title/Abstract]))"
    )
