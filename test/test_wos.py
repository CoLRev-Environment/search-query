#!/usr/bin/env python3
"""Web-of-Science query parser unit tests."""
import typing

import pytest

from search_query.constants import Colors
from search_query.constants import GENERAL_ERROR_POSITION
from search_query.constants import LinterMode
from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import ListQuerySyntaxError
from search_query.exception import SearchQueryException
from search_query.query import SearchField
from search_query.query_and import AndQuery
from search_query.query_or import OrQuery
from search_query.query_term import Term
from search_query.wos.parser import WOSListParser
from search_query.wos.parser import WOSParser

# ruff: noqa: E501
# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_str, expected_tokens",
    [
        (
            "TI=example AND AU=John Doe",
            [
                Token(value="TI=", type=TokenTypes.FIELD, position=(0, 3)),
                Token(value="example", type=TokenTypes.SEARCH_TERM, position=(3, 10)),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(11, 14)),
                Token(value="AU=", type=TokenTypes.FIELD, position=(15, 18)),
                Token(value="John Doe", type=TokenTypes.SEARCH_TERM, position=(18, 26)),
            ],
        ),
        (
            "TI=example example2 AND AU=John Doe",
            [
                Token(value="TI=", type=TokenTypes.FIELD, position=(0, 3)),
                Token(
                    value="example example2",
                    type=TokenTypes.SEARCH_TERM,
                    position=(3, 19),
                ),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(20, 23)),
                Token(value="AU=", type=TokenTypes.FIELD, position=(24, 27)),
                Token(value="John Doe", type=TokenTypes.SEARCH_TERM, position=(27, 35)),
            ],
        ),
        (
            "TI=example example2 example3 AND AU=John Doe",
            [
                Token(value="TI=", type=TokenTypes.FIELD, position=(0, 3)),
                Token(
                    value="example example2 example3",
                    type=TokenTypes.SEARCH_TERM,
                    position=(3, 28),
                ),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(29, 32)),
                Token(value="AU=", type=TokenTypes.FIELD, position=(33, 36)),
                Token(value="John Doe", type=TokenTypes.SEARCH_TERM, position=(36, 44)),
            ],
        ),
        (
            "TI=ex$mple* AND AU=John?Doe",
            [
                Token(value="TI=", type=TokenTypes.FIELD, position=(0, 3)),
                Token(value="ex$mple*", type=TokenTypes.SEARCH_TERM, position=(3, 11)),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(12, 15)),
                Token(value="AU=", type=TokenTypes.FIELD, position=(16, 19)),
                Token(value="John?Doe", type=TokenTypes.SEARCH_TERM, position=(19, 27)),
            ],
        ),
        (
            'direction*OR (route AND test)"',
            [
                Token(
                    value="direction*", type=TokenTypes.SEARCH_TERM, position=(0, 10)
                ),
                Token(value="OR", type=TokenTypes.LOGIC_OPERATOR, position=(10, 12)),
                Token(value="(", type=TokenTypes.PARENTHESIS_OPEN, position=(13, 14)),
                Token(value="route", type=TokenTypes.SEARCH_TERM, position=(14, 19)),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(20, 23)),
                Token(value="test", type=TokenTypes.SEARCH_TERM, position=(24, 28)),
                Token(value=")", type=TokenTypes.PARENTHESIS_CLOSED, position=(28, 29)),
            ],
        ),
    ],
)
def test_tokenization(query_str: str, expected_tokens: list) -> None:
    parser = WOSParser(query_str=query_str, search_field_general="", mode="")
    parser.tokenize()
    assert parser.tokens == expected_tokens, print(parser.tokens)


@pytest.mark.parametrize(
    "query_str, expected_messages",
    [
        (
            "test query",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "",
                }
            ],
        ),
        (
            "(test query)",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "",
                }
            ],
        ),
        (
            r"collaborat\* OR assistance",
            [
                {
                    "code": "E0004",
                    "label": "invalid-character",
                    "message": "Search term contains invalid character",
                    "is_fatal": False,
                    "position": [(0, 12)],
                    "details": "Invalid character '\\' in search term 'collaborat\\*'",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "",
                },
            ],
        ),
        (
            "(test query",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(0, 1)],
                    "details": "Unbalanced opening parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "",
                },
            ],
        ),
        (
            "test query)",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(10, 11)],
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "",
                },
            ],
        ),
        (
            "(test query))",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(12, 13)],
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "",
                },
            ],
        ),
        (
            "((test query)",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(0, 1)],
                    "details": "Unbalanced opening parenthesis",
                },
            ],
        ),
        (
            "TI=term1 AND OR",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(9, 15)],
                    "details": "Two operators in a row are not allowed.",
                },
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(13, 15)],
                    "details": "Cannot end with LOGIC_OPERATOR",
                },
                {
                    "code": "W0007",
                    "label": "implicit-precedence",
                    "message": "Operator changed at the same level (explicit parentheses are recommended)",
                    "is_fatal": False,
                    "position": [(9, 12), (13, 15)],
                    "details": "The query uses multiple operators with different precedence levels, but without parentheses to make the intended logic explicit. This can lead to unexpected interpretations of the query.\n\nSpecifically:\nOperator \x1b[92mAND\x1b[0m is evaluated first because it has the highest precedence level (1).\nOperator \x1b[93mOR\x1b[0m is evaluated last because it has the lowest precedence level (0).\n\nTo fix this, search-query adds artificial parentheses around operator groups with higher precedence.\n\n",
                },
            ],
        ),
        (
            "TI=term1 au= ti=",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(3, 12)],
                    "details": "",
                },
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(9, 16)],
                    "details": "",
                },
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(13, 16)],
                    "details": "Cannot end with FIELD",
                },
            ],
        ),
        (
            "TI=term1 (query)",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(3, 10)],
                    "details": "",
                }
            ],
        ),
        (
            ") (query)",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(0, 1)],
                    "details": "Cannot start with PARENTHESIS_CLOSED",
                },
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(0, 3)],
                    "details": "",
                },
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": [(0, 1)],
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "",
                },
            ],
        ),
        (
            "TI=term1 au=",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(3, 12)],
                    "details": "",
                },
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(9, 12)],
                    "details": "Cannot end with FIELD",
                },
            ],
        ),
        (
            "TI=term1 NEAR/20 term2",
            [
                {
                    "code": "F2007",
                    "label": "near-distance-too-large",
                    "message": "NEAR distance is too large (max: 15).",
                    "is_fatal": True,
                    "position": [(9, 16)],
                    "details": "",
                },
            ],
        ),
        # TODO: should be implemented properly.
        # (
        #     "TI=term1 NEAR/10 term2",
        #     [],
        # ),
        # TODO : should be implemented properly.
        # (
        #     "term1 NEAR term2",
        #     [],  # Assuming implicit NEAR distance is handled
        # ),
        # TODO : should be implemented properly.
        # (
        #     "term1 NEAR term2",  # Repeats earlier but for implicit NEAR warning
        #     [
        #         {
        #             "code": "W0006",
        #             "is_fatal": False,
        #             "details": "",
        #             "label": "implicit-near-value",
        #             "message": "The value of NEAR operator is implicit",
        #             "position": [( 6, 10 ],
        #         },
        #     ],
        # ),
        (
            "TI=term1 !term2",
            [
                {
                    "code": "F2001",
                    "label": "wildcard-unsupported",
                    "message": "Unsupported wildcard in search string.",
                    "is_fatal": True,
                    "position": [(9, 10)],
                    "details": "",
                },
            ],
        ),
        (
            'TI=term1 AND "?"',
            [
                {
                    "code": "F2006",
                    "label": "wildcard-standalone",
                    "message": "Wildcard cannot be standalone.",
                    "is_fatal": True,
                    "position": [(13, 16)],
                    "details": "",
                },
            ],
        ),
        (
            "TI=(term1 te?m2)",
            [],
        ),
        (
            "TI=(term1 term2*)",
            [],
        ),
        (
            "TI=(term1 term2!*)",
            [
                # TODO : should we raise only one message?
                {
                    "code": "F2005",
                    "label": "wildcard-after-special-char",
                    "message": "Wildcard cannot be preceded by special characters.",
                    "is_fatal": True,
                    "position": [(4, 17)],
                    "details": "",
                },
                {
                    "code": "F2001",
                    "label": "wildcard-unsupported",
                    "message": "Unsupported wildcard in search string.",
                    "is_fatal": True,
                    "position": [(15, 16)],
                    "details": "",
                },
            ],
        ),
        (
            "TI=te*",
            [
                {
                    "code": "F2003",
                    "is_fatal": True,
                    "details": "",
                    "label": "wildcard-right-short-length",
                    "message": "Right-hand wildcard must preceded by at least three characters.",
                    "position": [(3, 6)],
                },
            ],
        ),
        (
            "TI=term1 TI=*term2",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": [(3, 12)],
                    "details": "",
                }
            ],
        ),
        (
            "TI=*te",
            [
                {
                    "code": "F2004",
                    "is_fatal": True,
                    "details": "",
                    "label": "wildcard-left-short-length",
                    "message": "Left-hand wildcard must be preceded by at least three characters.",
                    "position": [(3, 6)],
                },
            ],
        ),
        (
            "IS=1234-5678",
            [],
        ),
        (
            "IS=1234-567",
            [
                {
                    "code": "F2008",
                    "is_fatal": True,
                    "details": "",
                    "label": "isbn-format-invalid",
                    "message": "Invalid ISBN format.",
                    "position": [(3, 11)],
                },
            ],
        ),
        (
            "IS=978-3-16-148410-0",
            [],
        ),
        (
            "IS=978-3-16-148410",
            [
                {
                    "code": "F2008",
                    "is_fatal": True,
                    "details": "",
                    "label": "isbn-format-invalid",
                    "message": "Invalid ISBN format.",
                    "position": [(3, 18)],
                },
            ],
        ),
        (
            "DO=10.1000/xyz123",
            [],
        ),
        (
            "DO=12.1000/xyz",
            [
                {
                    "code": "F2009",
                    "label": "doi-format-invalid",
                    "message": "Invalid DOI format.",
                    "is_fatal": True,
                    "position": [(3, 14)],
                    "details": "",
                },
            ],
        ),
        (
            "TI=term1 and TI=term2",
            [
                {
                    "code": "W0005",
                    "is_fatal": False,
                    "details": "",
                    "label": "operator-capitalization",
                    "message": "Operators should be capitalized",
                    "position": [(9, 12)],
                },
            ],
        ),
        (
            "TI=term1 AND PY=202*",
            [
                {
                    "code": "F2002",
                    "is_fatal": True,
                    "details": "",
                    "label": "wildcard-in-year",
                    "message": "Wildcard characters (*, ?, $) not supported in year search.",
                    "position": [(16, 20)],
                },
            ],
        ),
        (
            "TI=term1 AND PY=20xy",
            [
                {
                    "code": "F2014",
                    "label": "year-format-invalid",
                    "message": "Invalid year format.",
                    "is_fatal": True,
                    "position": [(16, 20)],
                    "details": "",
                }
            ],
        ),
        (
            "TI=term1 AND IY=digital",
            [
                {
                    "code": "F2011",
                    "label": "search-field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "position": [(13, 16)],
                    "details": "Search field IY= at position (13, 16) is not supported. Supported fields for PLATFORM.WOS: ab=|abstract=|la=|language=|ad=|address=|all=|all fields=|ai=|author identifiers=|ak=|author keywords=|au=|author=|cf=|conference=|ci=|city=|cu=|country/region=|do=|doi=|ed=|editor=|fg=|grant number=|fo=|funding agency=|ft=|funding text=|gp=|group author=|is=|issn/isbn=|kp=|keywords plus=|og=|organization - enhanced=|oo=|organization=|pmid=|pubmed id=|ps=|province/state=|py=|year published=|sa=|street address=|sg=|suborganization=|so=|publication name=|su=|research area=|ti=|title=|ts=|topic=|ut=|accession number=|wc=|web of science category=|zp=|zip/postal code=",
                }
            ],
        ),
        (
            "TI=term1 AND PY=1900-2000",
            [
                {
                    "code": "F2010",
                    "label": "year-span-violation",
                    "message": "Year span must be five or less.",
                    "is_fatal": True,
                    "position": [(16, 25)],
                    "details": "",
                },
            ],
        ),
        (
            "term1 AND ehealth[ti]",
            [
                {
                    "code": "F1010",
                    "label": "invalid-syntax",
                    "message": "Query contains invalid syntax",
                    "is_fatal": True,
                    "position": [(17, 21)],
                    "details": "WOS fields must be before search terms and without brackets, e.g. AB=robot or TI=monitor. '[ti]' is invalid.",
                },
                {
                    "code": "F0001",
                    "label": "tokenizing-failed",
                    "message": "Fatal error during tokenization",
                    "is_fatal": True,
                    "position": [(9, 21)],
                    "details": "Unparsed segment: 'ehealth[ti]'",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": [(-1, -1)],
                    "details": "",
                },
            ],
        ),
        (
            "TI=term1*ending",
            [],
        ),
        (
            # Note: should raise an exception for invalid truncation according to:
            # https://images.webofknowledge.com/WOKRS528R6/help/TCT/ht_errors.html#error_invalid_truncation
            # But: testing it in the interface does not raise an error.
            "TS=*arbon",
            [],
        ),
        (
            "PY=200*",
            [
                {
                    "code": "F2012",
                    "label": "year-without-search-terms",
                    "message": "A search for publication years must include at least another search term.",
                    "is_fatal": True,
                    "position": [(0, 7)],
                    "details": "",
                },
                {
                    "code": "F2002",
                    "label": "wildcard-in-year",
                    "message": "Wildcard characters (*, ?, $) not supported in year search.",
                    "is_fatal": True,
                    "position": [(3, 7)],
                    "details": "",
                },
            ],
        ),
        (
            "TS=ca*",
            [
                {
                    "code": "F2003",
                    "label": "wildcard-right-short-length",
                    "message": "Right-hand wildcard must preceded by at least three characters.",
                    "is_fatal": True,
                    "position": [(3, 6)],
                    "details": "",
                }
            ],
        ),
        (
            "TS=“carbon”",
            [
                {
                    "code": "W0013",
                    "label": "non-standard-quotes",
                    "message": "Non-standard quotes",
                    "is_fatal": False,
                    "position": [(3, 4), (10, 11)],
                    "details": "Non-standard quotes found: “”",
                }
            ],
        ),
        (
            "ALL=(term1 OR term2 OR term3 OR term4 OR term5 OR term6 OR term7 OR term8 OR term9 OR term10 OR term11 OR term12 OR term13 OR term14 OR term15 OR term16 OR term17 OR term18 OR term19 OR term20 OR term21 OR term22 OR term23 OR term24 OR term25 OR term26 OR term27 OR term28 OR term29 OR term30 OR term31 OR term32 OR term33 OR term34 OR term35 OR term36 OR term37 OR term38 OR term39 OR term40 OR term41 OR term42 OR term43 OR term44 OR term45 OR term46 OR term47 OR term48 OR term49 OR term50 OR term51 OR term52)",
            [
                {
                    "code": "F1012",
                    "label": "too-many-search-terms",
                    "message": "Too many search terms in the query",
                    "is_fatal": True,
                    "position": [(5, 512)],
                    "details": "The maximum number of search terms (for ALL Fields) is 50.",
                }
            ],
        ),
        (
            # Note: this is equivalent to the prevous one, but it does not raise an error in the web of science interface?!.
            "ALL=term1 OR ALL=term2 OR ALL=term3 OR ALL=term4 OR ALL=term5 OR ALL=term6 OR ALL=term7 OR ALL=term8 OR ALL=term9 OR ALL=term10 OR ALL=term11 OR ALL=term12 OR ALL=term13 OR ALL=term14 OR ALL=term15 OR ALL=term16 OR ALL=term17 OR ALL=term18 OR ALL=term19 OR ALL=term20 OR ALL=term21 OR ALL=term22 OR ALL=term23 OR ALL=term24 OR ALL=term25 OR ALL=term26 OR ALL=term27 OR ALL=term28 OR ALL=term29 OR ALL=term30 OR ALL=term31 OR ALL=term32 OR ALL=term33 OR ALL=term34 OR ALL=term35 OR ALL=term36 OR ALL=term37 OR ALL=term38 OR ALL=term39 OR ALL=term40 OR ALL=term41 OR ALL=term42 OR ALL=term43 OR ALL=term44 OR ALL=term45 OR ALL=term46 OR ALL=term47 OR ALL=term48 OR ALL=term49 OR ALL=term50 OR ALL=term51 OR ALL=term52",
            [
                {
                    "code": "F1012",
                    "label": "too-many-search-terms",
                    "message": "Too many search terms in the query",
                    "is_fatal": True,
                    "position": [(0, 715)],
                    "details": "The maximum number of search terms (for ALL Fields) is 50.",
                }
            ],
        ),
        (
            "TS=(activity) AND (TS=(cancer) AND SO=(Lancet))",
            [
                {
                    "code": "W0014",
                    "label": "journal-filter-in-subquery",
                    "message": "Journal (or publication name) filter in subquery",
                    "is_fatal": False,
                    "position": [(39, 45)],
                    "details": "Please double-check whether journal/publication-name filters (SO=) should apply to the entire query.",
                }
            ],
        ),
    ],
)
def test_linter(
    query_str: str,
    expected_messages: typing.List[dict],
) -> None:
    print(query_str)

    parser = WOSParser(query_str)
    try:
        parser.parse()
    except SearchQueryException:
        pass
    parser.print_tokens()
    print(parser.linter.messages)
    assert parser.linter.messages == expected_messages


@pytest.mark.parametrize(
    "query_str, expected_query",
    [
        (
            "TI=(term1 OR term2 AND term3)",
            "OR[TI=][term1, AND[term2, term3]]",
        ),
        (
            "TI=term1 AND TI=term2 OR TI=term3",
            "OR[AND[term1[TI=], term2[TI=]], term3[TI=]]",
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
def test_implicit_precedence(query_str: str, expected_query: str) -> None:
    print(query_str)
    parser = WOSParser(query_str, mode=LinterMode.NONSTRICT)
    query = parser.parse()
    parser.print_tokens()

    print(f"{Colors.GREEN}{query.to_generic_string()}{Colors.END}")
    assert expected_query == query.to_generic_string()

    print(parser.linter.messages)
    assert len(parser.linter.messages) == 1
    msg = parser.linter.messages[0]

    assert msg["code"] == "W0007"
    assert msg["label"] == "implicit-precedence"
    assert msg["is_fatal"] is False


def test_query_parsing_basic_vs_advanced() -> None:
    # Basic search
    parser = WOSParser(
        query_str="digital AND online", search_field_general="All Fields", mode=""
    )
    parser.parse()
    assert len(parser.linter.messages) == 0

    # Search field could be nested
    parser = WOSParser(
        query_str="(TI=digital AND AB=online)",
        search_field_general="All Fields",
        mode="",
    )
    parser.parse()
    assert len(parser.linter.messages) == 0

    # Advanced search
    parser = WOSParser(
        query_str="ALL=(digital AND online)", search_field_general="", mode=""
    )
    parser.parse()
    assert len(parser.linter.messages) == 0

    parser = WOSParser(
        query_str="(ALL=digital AND ALL=online)", search_field_general="", mode=""
    )
    parser.parse()
    assert len(parser.linter.messages) == 0

    # ERROR: Basic search without search_field_general
    parser = WOSParser(query_str="digital AND online", search_field_general="", mode="")
    parser.parse()
    assert len(parser.linter.messages) == 1

    # ERROR: Advanced search with search_field_general
    parser = WOSParser(
        query_str="ALL=(digital AND online)", search_field_general="All Fields", mode=""
    )
    parser.parse()
    assert len(parser.linter.messages) == 1
    print(parser.linter.messages)

    # ERROR: Advanced search with search_field_general
    parser = WOSParser(
        query_str="TI=(digital AND online)", search_field_general="All Fields", mode=""
    )
    parser.parse()
    assert len(parser.linter.messages) == 1
    assert parser.linter.messages[0] == {
        "code": "E0002",
        "label": "search-field-contradiction",
        "message": "Contradictory search fields specified",
        "is_fatal": False,
        "details": "",
        "position": [(0, 3)],
    }


@pytest.mark.parametrize(
    "query_str, expected_translation",
    [
        (
            "TS=(eHealth) AND TS=(Review)",
            "AND[eHealth[TS=], Review[TS=]]",
        ),
        (
            'TS=("cancer treatment") NOT TS=("chemotherapy")',
            'NOT["cancer treatment"[TS=], "chemotherapy"[TS=]]',
        ),
        (
            'TS=("cancer treatment" NOT "chemotherapy")',
            'NOT[TS=]["cancer treatment", "chemotherapy"]',
        ),
        (
            'TS=("cancer treatment") NOT TS=("chemotherapy" OR "radiation")',
            'NOT["cancer treatment"[TS=], OR[TS=]["chemotherapy", "radiation"]]',
        ),
        (
            'TS=("deep learning" NEAR/3 "image analysis") AND TS=("MRI" NEAR "brain")',
            'AND[NEAR/3[TS=]["deep learning", "image analysis"], NEAR/15[TS=]["MRI", "brain"]]',
        ),
    ],
)
def test_parser_wos(query_str: str, expected_translation: str) -> None:
    print(query_str)
    wos_parser = WOSParser(query_str)
    query_tree = wos_parser.parse()
    assert expected_translation == query_tree.to_generic_string(), print(
        query_tree.to_generic_string()
    )


def test_query_in_quotes() -> None:
    parser = WOSParser(
        query_str='"TI=(digital AND online)"', search_field_general="", mode=""
    )
    parser.parse()

    # Assertions using standard assert statement
    assert len(parser.linter.messages) == 1
    assert parser.tokens[0].value == "TI="


def test_artificial_parentheses() -> None:
    parser = WOSParser(
        query_str="remote OR online AND work",
        search_field_general="All Fields",
        mode="",
    )
    query = parser.parse()

    # Assertions using standard assert statement
    assert query.value == "OR"
    assert query.children[0].value == "remote"
    assert query.children[1].value == "AND"
    assert query.children[1].children[0].value == "online"
    assert query.children[1].children[1].value == "work"

    # Check if linter messages contain one entry
    assert len(parser.linter.messages) == 1
    assert parser.linter.messages[0] == {
        "code": "W0007",
        "label": "implicit-precedence",
        "message": "Operator changed at the same level (explicit parentheses are recommended)",
        "is_fatal": False,
        "position": [(7, 9), (17, 20)],
        "details": "The query uses multiple operators with different precedence levels, but without parentheses to make the intended logic explicit. This can lead to unexpected interpretations of the query.\n\nSpecifically:\nOperator \x1b[92mAND\x1b[0m is evaluated first because it has the highest precedence level (1).\nOperator \x1b[93mOR\x1b[0m is evaluated last because it has the lowest precedence level (0).\n\nTo fix this, search-query adds artificial parentheses around operator groups with higher precedence.\n\n",
    }
    assert query.to_generic_string() == "OR[ALL=][remote, AND[online, work]]"


# Test case 1
def test_list_parser_case_1() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*" OR "Distributed leader*" OR "Distributive leader*" OR "Collaborate leader*" OR "Collaborative leader*" OR "Team leader*" OR "Peer-led" OR "Athlete leader*" OR "Team captain*" OR "Peer mentor*" OR "Peer Coach")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats" OR "acrobatic" OR "aikido" OR "aikidoists" OR "anetso" OR "archer" OR "archers" OR "archery" OR "airsoft" OR "angling" OR "aquatics" OR "aerobics" OR "athlete" OR "athletes" OR "athletic" OR "athletics" OR "ball game*" OR "ballooning" OR "basque pelota" OR "behcup" OR "bicycling" OR "BMX" OR "bodyboarding" OR "boule lyonnaise" OR "bridge" OR "badminton" OR "balle au tamis" OR "baseball" OR "basketball" OR "battle ball" OR "battleball" OR "biathlon" OR "billiards" OR "boating" OR "bobsledding" OR "bobsled" OR "bobsledder" OR "bobsledders" OR "bobsleigh" OR "boccia" OR "bocce" OR "buzkashi" OR "bodybuilding" OR "bodybuilder" OR "bodybuilders" OR "bowling" OR "bowler" OR "bowlers" OR "bowls" OR "boxing" OR "boxer" OR "boxers" OR "bandy" OR "breaking" OR "breakdanc*" OR "broomball" OR "budo" OR "bullfighting" OR "bullfights" OR "bullfight" OR "bullfighter" OR "bullfighters" OR "mountain biking" OR "mountain bike" OR "carom billiards" OR "camogie" OR "canoe slalom" OR "canoeing" OR "canoeist" OR "canoeists" OR "canoe" OR "climbing" OR "coasting" OR "cricket" OR "croquet" OR "crossfit" OR "curling" OR "curlers" OR "curler" OR "cyclist" OR "cyclists" OR "combat*" OR "casting" OR "cheerleading" OR "cheer" OR "cheerleader*" OR "chess" OR "charrerias" OR "cycling" OR "dancesport" OR "darts" OR "decathlon" OR "draughts" OR "dancing" OR "dance" OR "dancers" OR "dancer" OR "diving" OR "dodgeball" OR "e-sport" OR "dressage" OR "endurance" OR "equestrian" OR "eventing" OR "eskrima" OR "escrima" OR "fencer" OR "fencing" OR "fencers" OR "fishing" OR "finswimming" OR "fistball" OR "floorball" OR "flying disc" OR "foosball" OR "futsal" OR "flickerball" OR "football" OR "frisbee" OR "gliding" OR "go" OR "gongfu" OR "gong fu" OR "goalball" OR "golf" OR "golfer" OR "golfers" OR "gymnast" OR "gymnasts" OR "gymnastics" OR "gymnastic" OR "gymkhanas" OR "half rubber" OR "highland games" OR "hap ki do" OR "halfrubber" OR "handball" OR "handballers" OR "handballer" OR "hapkido" OR "hiking" OR "hockey" OR "hsing-I" OR "hurling" OR "Hwa rang do" OR "hwarangdo" OR "horsemanship" OR "horseshoes" OR "orienteer" OR "orienteers" OR "orienteering" OR "iaido" OR "iceboating" OR "icestock" OR "intercrosse" OR "jousting" OR "jai alai" OR "jeet kune do" OR "jianzi" OR "jiu-jitsu" OR "jujutsu" OR "ju-jitsu" OR "kung fu" OR "kungfu" OR "kenpo" OR "judo" OR "judoka" OR "judoists" OR "judoist" OR "jump" OR "jumping" OR "jumper" OR "jian zi" OR "kabaddi" OR "kajukenbo" OR "karate" OR "karateists" OR "karateist" OR "karateka" OR "kayaking" OR "kendo" OR "kenjutsu" OR "kickball" OR "kickbox*" OR "kneeboarding" OR "krav maga" OR "kuk sool won" OR "kun-tao" OR "kuntao" OR "kyudo" OR "korfball" OR "lacrosse" OR "life saving" OR "lapta" OR "lawn tempest" OR "bowling" OR "bowls" OR "logrolling" OR "luge" OR "marathon" OR "marathons" OR "marathoning" OR "martial art" OR "martial arts" OR "martial artist" OR "martial artists" OR "motorsports" OR "mountainboarding" OR "mountain boarding" OR "mountaineer" OR "mountaineering" OR "mountaineers" OR "muay thai" OR "mallakhamb" OR "motorcross" OR "modern arnis" OR "naginata do" OR "netball" OR "ninepins" OR "nine-pins" OR "nordic combined" OR "nunchaku" OR "olympic*" OR "pes\u00e4pallo" OR "pitch and putt" OR "pool" OR "pato" OR "paddleball" OR "paddleboarding" OR "pankration" OR "pancratium" OR "parachuting" OR "paragliding" OR "paramotoring" OR "paraski" OR "paraskiing" OR "paraskier" OR "paraskier" OR "parakour" OR "pelota" OR "pencak silat" OR "pentathlon" OR "p\u00e9tanque" OR "petanque" OR "pickleball" OR "pilota" OR "pole bending" OR "pole vault" OR "polo" OR "polocrosse" OR "powerlifting" OR "player*" OR "powerboating" OR "pegging" OR "parathletic" OR "parathletics" OR "parasport*" OR "paraathletes" OR "paraathlete" OR "pushball" OR "push ball" OR "quidditch" OR "races" OR "race" OR "racing" OR "racewalking" OR "racewalker" OR "racewalkers" OR "rackets" OR "racketlon" OR "racquetball" OR "racquet" OR "racquets" OR "rafting" OR "regattas" OR "riding" OR "ringette" OR "rock-it-ball" OR "rogaining" OR "rock climbing" OR "roll ball" OR "roller derby" OR "roping" OR "rodeos" OR "rodeo" OR "riding" OR "rider" OR "riders" OR "rounders" OR "rowing" OR "rower" OR "rowers" OR "rug ball" OR "running" OR "runner" OR "runners" OR "rugby" OR "sailing" OR "san shou" OR "sepaktakraw" OR "sepak takraw" OR "san-jitsu" OR "savate" OR "shinty" OR "shishimai" OR "shooting" OR "singlestick" OR "single stick" OR "skateboarding" OR "skateboarder" OR "skateboarders" OR "skater" OR "skaters" OR "skating" OR "skipping" OR "racket game*" OR "rollerskating" OR "skelton" OR "skibobbing" OR "ski" OR "skiing" OR "skier" OR "skiers" OR "skydive" OR "skydiving" OR "skydivers" OR "skydiver" OR "skysurfing" OR "sledding" OR "sledging" OR "sled dog" OR "sleddog" OR "snooker" OR "sleighing" OR "snowboarder" OR "snowboarding" OR "snowboarders" OR "snowshoeing" OR "soccer" OR "softball" OR "spear fighting" OR "speed-a-way" OR "speedball" OR "sprint" OR "sprinting" OR "sprints" OR "squash" OR "stick fighting" OR "stickball" OR "stoolball" OR "stunt flying" OR "sumo" OR "surfing" OR "surfer" OR "surfers" OR "swimnastics" OR "swimming" OR "snowmobiling" OR "swim" OR "swimmer" OR "swimmers" OR "shot-put" OR "shot-putters" OR "shot-putter" OR "sport" OR "sports" OR "tae kwon do" OR "taekwondo" OR "taekgyeon" OR "taekkyeon" OR "taekkyon" OR "taekyun" OR "tang soo do" OR "tchoukball" OR "tennis" OR "tetherball" OR "throwing" OR "thrower" OR "throwers" OR "tai ji" OR "tai chi" OR "taiji" OR "t ai chi" OR "throwball" OR "tug of war" OR "tobogganing" OR "track and field" OR "track & field" OR "trampoline" OR "trampolining" OR "trampolinists" OR "trampolinist" OR "trapball" OR "trapshooting" OR "triathlon" OR "triathlete" OR "triathletes" OR "tubing" OR "tumbling" OR "vaulting" OR "volleyball" OR "wakeboarding" OR "wallyball" OR "weightlifting" OR "weightlifter" OR "weightlifters" OR "wiffle ball" OR "windsurfing" OR "windsurfer" OR "windsurfers" OR "walking" OR "wingwalking" OR "woodchopping" OR "wood chopping" OR "woodball" OR "wushu" OR "weight lifter" OR "weight lift" OR "weight lifters" OR "wrestling" OR "wrestler" OR "wrestlers" OR "vovinam" OR "vx" OR "yoga")\n3. #1 AND #2\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    list_parser.parse()


# Test case 2
def test_list_parser_case_2() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats")'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    try:
        list_parser.parse()
    except ListQuerySyntaxError:
        pass
    assert list_parser.linter.messages[GENERAL_ERROR_POSITION][0] == {
        "code": "F3001",
        "is_fatal": True,
        "label": "missing-root-node",
        "message": "List format query without root node (typically containing operators)",
        "position": [(-1, -1)],
        "details": "",
    }


# Test case 3
def test_list_parser_case_3() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats")\n3. #1 AND #4\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    try:
        list_parser.parse()
    except ListQuerySyntaxError as exc:
        print(exc)
    assert list_parser.linter.messages == {
        2: [
            {
                "code": "F3003",
                "label": "invalid-list-reference",
                "message": "Invalid list reference in list query",
                "is_fatal": True,
                "position": [(101, 103)],
                "details": "List reference #4 not found.",
            }
        ]
    }


# Test case 4
def test_list_parser_case_4() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*" OR "Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats" OR "acrobatics" OR "acrobat" OR "acrobats")\n3. #1 AND #2\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    query = list_parser.parse()
    print(query.to_string())
    assert (
        query.to_string()
        == 'TS=("Peer leader*" OR "Shared leader*" OR "Peer leader*" OR "Shared leader*") AND TS=("acrobatics" OR "acrobat" OR "acrobats" OR "acrobatics" OR "acrobat" OR "acrobats")'
    )
    print(list_parser.linter.messages)
    assert list_parser.linter.messages == {
        -1: [],
        "1": [
            {
                "code": "W0004",
                "label": "query-structure-unnecessarily-complex",
                "message": "Query structure is more complex than necessary",
                "is_fatal": False,
                "position": [(7, 21), (45, 59)],
                "details": 'Term "Peer leader*" is contained multiple times i.e., redundantly.',
            },
            {
                "code": "W0004",
                "label": "query-structure-unnecessarily-complex",
                "message": "Query structure is more complex than necessary",
                "is_fatal": False,
                "position": [(25, 41), (63, 79)],
                "details": 'Term "Shared leader*" is contained multiple times i.e., redundantly.',
            },
        ],
        "2": [
            {
                "code": "W0004",
                "label": "query-structure-unnecessarily-complex",
                "message": "Query structure is more complex than necessary",
                "is_fatal": False,
                "position": [(88, 100), (131, 143)],
                "details": 'Term "acrobatics" is contained multiple times i.e., redundantly.',
            },
            {
                "code": "W0004",
                "label": "query-structure-unnecessarily-complex",
                "message": "Query structure is more complex than necessary",
                "is_fatal": False,
                "position": [(104, 113), (147, 156)],
                "details": 'Term "acrobat" is contained multiple times i.e., redundantly.',
            },
            {
                "code": "W0004",
                "label": "query-structure-unnecessarily-complex",
                "message": "Query structure is more complex than necessary",
                "is_fatal": False,
                "position": [(117, 127), (160, 170)],
                "details": 'Term "acrobats" is contained multiple times i.e., redundantly.',
            },
        ],
    }


# Test case 5
def test_list_parser_case_5() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats")\n3. #1 AND #2 AND\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    try:
        list_parser.parse()
    except ListQuerySyntaxError as exc:
        print(exc)
    print(list_parser.linter.messages)
    assert list_parser.linter.messages == {
        -1: [
            {
                "code": "F1004",
                "label": "invalid-token-sequence",
                "message": "The sequence of tokens is invalid.",
                "is_fatal": True,
                "position": [(104, 107)],
                "details": "Last token of query item 3 must be a list item.",
            }
        ]
    }


# Test case 6
def test_list_parser_case_6() -> None:
    query_list = "1. TS=(inflammatory bowel diseases OR (inflamm* AND bowel*) OR (ulcer* colitis) OR crohn OR crohns OR ileitis or ileocolitis OR granulomatous enteritis OR proctocolitis OR regional enteritis OR rectosigmoiditis)\n2. TS=(prebiotic* OR synbiotic OR inulin OR galactan* or *oligosacc* OR pectin)\n3. TS=(interven* OR trial* or study)\n4. #3 AND #2 AND #1\n"

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    query = list_parser.parse()
    print(query.to_string())
    # Note: parentheses for inflamm* AND bowl* are missing?
    assert (
        query.to_string()
        == "TS=(interven* OR trial* OR study) AND TS=(prebiotic* OR synbiotic OR inulin OR galactan* OR *oligosacc* OR pectin) AND TS=(inflammatory bowel diseases OR (inflamm* AND bowel*) OR ulcer* colitis OR crohn OR crohns OR ileitis OR ileocolitis OR granulomatous enteritis OR proctocolitis OR regional enteritis OR rectosigmoiditis)"
    )
    print(list_parser.linter.messages)
    assert list_parser.linter.messages == {
        -1: [],
        "3": [
            {
                "code": "W0005",
                "label": "operator-capitalization",
                "message": "Operators should be capitalized",
                "is_fatal": False,
                "position": [(319, 321)],
                "details": "",
            }
        ],
        "2": [
            {
                "code": "W0005",
                "label": "operator-capitalization",
                "message": "Operators should be capitalized",
                "is_fatal": False,
                "position": [(266, 268)],
                "details": "",
            }
        ],
        "1": [
            {
                "code": "W0005",
                "label": "operator-capitalization",
                "message": "Operators should be capitalized",
                "is_fatal": False,
                "position": [(110, 112)],
                "details": "",
            }
        ],
    }


def test_wos_valid_query() -> None:
    """Should pass WOS constraints."""
    # This should NOT raise
    OrQuery(
        children=[
            Term(
                value="AI",
                search_field=SearchField("TI="),
                platform=PLATFORM.WOS.value,
            ),
            Term(
                value="ethics",
                search_field=SearchField("AB="),
                platform=PLATFORM.WOS.value,
            ),
        ],
        platform=PLATFORM.WOS.value,
    )


def test_wos_invalid_nested_with_operator_field() -> None:
    """Should raise: nested operator with search_field set."""
    with pytest.raises(Exception):
        AndQuery(
            [
                Term(
                    value="DE12",
                    search_field=SearchField("IS="),
                    platform=PLATFORM.WOS.value,
                ),
                Term(
                    value="ethics",
                    search_field=SearchField("AB"),
                    platform=PLATFORM.WOS.value,
                ),
            ],
            search_field=SearchField("TI"),
            platform=PLATFORM.WOS.value,
        )


def test_wos_invalid_fields() -> None:
    """Should raise: invalid search fields (e.g., brackets or missing =)"""
    with pytest.raises(Exception):
        AndQuery(
            [
                Term(
                    value="DE12",
                    search_field=SearchField("[ti]"),
                    platform=PLATFORM.WOS.value,
                ),
                Term(
                    value="ethics",
                    search_field=SearchField("AB="),
                    platform=PLATFORM.WOS.value,
                ),
            ],
            search_field=SearchField("TI="),
            platform=PLATFORM.WOS.value,
        )


@pytest.mark.parametrize(
    "query_str, search_field_general, expected_parsed",
    [
        (
            "eHealth AND Review",
            "Title",
            "AND[TI=][eHealth, Review]",
        ),
    ],
)
def test_parser(
    query_str: str, search_field_general: str, expected_parsed: str
) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = WOSParser(query_str, search_field_general=search_field_general)
    query = parser.parse()

    assert expected_parsed == query.to_generic_string(), print(
        query.to_generic_string()
    )
