#!/usr/bin/env python3
"""Web-of-Science query parser unit tests."""
import typing

import pytest

from search_query.constants import Colors
from search_query.constants import GENERAL_ERROR_POSITION
from search_query.constants import LinterMode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import ListQuerySyntaxError
from search_query.exception import SearchQueryException
from search_query.parser_wos import WOSListParser
from search_query.parser_wos import WOSParser

# ruff: noqa: E501
# flake8: noqa: E501

# ruff: noqa: E501
# pylint: disable=too-many-lines
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
                    "position": (-1, -1),
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
                    "position": (-1, -1),
                    "details": "",
                }
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
                    "position": (0, 1),
                    "details": "Unbalanced opening parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
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
                    "position": (10, 11),
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
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
                    "position": (12, 13),
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
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
                    "position": (0, 1),
                    "details": "Unbalanced opening parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
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
                    "position": (9, 15),
                    "details": "Two operators in a row are not allowed.",
                },
                {
                    "code": "W0007",
                    "label": "implicit-precedence",
                    "message": "Operator changed at the same level (explicit parentheses are recommended)",
                    "is_fatal": False,
                    "position": (13, 15),
                    "details": "",
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
                    "position": (9, 12),
                    "details": "",
                },
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (13, 16),
                    "details": "",
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
                    "position": (9, 10),
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
                    "position": (2, 3),
                    "details": "",
                },
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (0, 1),
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
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
                    "position": (9, 12),
                    "details": "",
                }
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
                    "position": (9, 16),
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
        #             "position": (6, 10),
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
                    "position": (9, 10),
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
                    "position": (13, 16),
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
                    "position": (4, 17),
                    "details": "",
                },
                {
                    "code": "F2001",
                    "label": "wildcard-unsupported",
                    "message": "Unsupported wildcard in search string.",
                    "is_fatal": True,
                    "position": (15, 16),
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
                    "position": (3, 6),
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
                    "position": (9, 12),
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
                    "position": (3, 6),
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
                    "position": (3, 11),
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
                    "position": (3, 18),
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
                    "position": (3, 14),
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
                    "position": (9, 12),
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
                    "position": (16, 20),
                },
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
                    "details": "Search field IY= at position (13, 16) is not supported.",
                    "position": (13, 16),
                },
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
                    "position": (16, 25),
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
                    "position": (17, 21),
                    "details": "WOS fields must be before search terms and without brackets, e.g. AB=robot or TI=monitor. '[ti]' is invalid.",
                },
                {
                    "code": "F0001",
                    "label": "tokenizing-failed",
                    "message": "Fatal error during tokenization",
                    "is_fatal": True,
                    "position": (9, 21),
                    "details": "Unparsed segment: 'ehealth[ti]'",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
                },
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
            "TI=term1 AND term2 OR term3",
            "OR[AND[term1[TI=], term2], term3]",
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
    parser = WOSParser(query_str, mode=LinterMode.NONSTRICT)
    query = parser.parse()
    parser.print_tokens()

    print(f"{Colors.GREEN}{query.to_generic_string()}{Colors.END}")
    assert expected_query == query.to_generic_string()

    assert len(parser.linter.messages) == 1
    msg = parser.linter.messages[0]

    assert msg["code"] == "W0007"
    assert msg["label"] == "implicit-precedence"
    assert msg["is_fatal"] is False
    assert msg["details"] == ""


def test_query_parsing_basic_vs_advanced() -> None:
    # Basic search
    parser = WOSParser(
        query_str="digital AND online", search_field_general="ALL=", mode=""
    )
    parser.parse()
    assert len(parser.linter.messages) == 0

    # Search field could be nested
    parser = WOSParser(
        query_str="(TI=digital AND AB=online)", search_field_general="ALL=", mode=""
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
        query_str="ALL=(digital AND online)", search_field_general="ALL=", mode=""
    )
    parser.parse()
    assert len(parser.linter.messages) == 1

    # ERROR: Advanced search with search_field_general
    parser = WOSParser(
        query_str="TI=(digital AND online)", search_field_general="ALL=", mode=""
    )
    parser.parse()
    assert len(parser.linter.messages) == 1
    assert parser.linter.messages[0] == {
        "code": "E0002",
        "label": "search-field-contradiction",
        "message": "Contradictory search fields specified",
        "is_fatal": False,
        "details": "",
        "position": (0, 3),
    }


@pytest.mark.parametrize(
    "query_str, expected_translation",
    [
        (
            "TS=(eHealth) AND TS=(Review)",
            "AND[eHealth[TS=], Review[TS=]]",
        ),
    ],
)
def test_parser_wos(query_str: str, expected_translation: str) -> None:
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
        query_str="remote OR online AND work", search_field_general="ALL=", mode=""
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
        "position": (7, 9),
        "is_fatal": False,
        "details": "",
    }
    assert query.to_generic_string() == "OR[ALL=][remote, AND[online, work]]"


# Test case 1
def test_list_parser_case_1() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*" OR "Distributed leader*" OR \u201cDistributive leader*\u201d OR \u201cCollaborate leader*\u201d OR "Collaborative leader*" OR "Team leader*" OR "Peer-led" OR "Athlete leader*" OR "Team captain*" OR "Peer mentor*" OR "Peer Coach")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats" OR "acrobatic" OR "aikido" OR "aikidoists" OR "anetso" OR "archer" OR "archers" OR "archery" OR "airsoft" OR "angling" OR "aquatics" OR "aerobics" OR "athlete" OR "athletes" OR "athletic" OR "athletics" OR "ball game*" OR "ballooning" OR "basque pelota" OR "behcup" OR "bicycling" OR "BMX" OR "bodyboarding" OR "boule lyonnaise" OR "bridge" OR "badminton" OR "balle au tamis" OR "baseball" OR "basketball" OR "battle ball" OR "battleball" OR "biathlon" OR "billiards" OR "boating" OR "bobsledding" OR "bobsled" OR "bobsledder" OR "bobsledders" OR "bobsleigh" OR "boccia" OR "bocce" OR "buzkashi" OR "bodybuilding" OR "bodybuilder" OR "bodybuilders" OR "bowling" OR "bowler" OR "bowlers" OR "bowls" OR "boxing" OR "boxer" OR "boxers" OR "bandy" OR "breaking" OR "breakdanc*" OR "broomball" OR "budo" OR "bullfighting" OR "bullfights" OR "bullfight" OR "bullfighter" OR "bullfighters" OR "mountain biking" OR "mountain bike" OR "carom billiards" OR "camogie" OR "canoe slalom" OR "canoeing" OR "canoeist" OR "canoeists" OR "canoe" OR "climbing" OR "coasting" OR "cricket" OR "croquet" OR "crossfit" OR "curling" OR "curlers" OR "curler" OR "cyclist" OR "cyclists" OR "combat*" OR "casting" OR "cheerleading" OR "cheer" OR "cheerleader*" OR "chess" OR "charrerias" OR "cycling" OR "dancesport" OR "darts" OR "decathlon" OR "draughts" OR "dancing" OR "dance" OR "dancers" OR "dancer" OR "diving" OR "dodgeball" OR "e-sport" OR "dressage" OR "endurance" OR "equestrian" OR "eventing" OR "eskrima" OR "escrima" OR "fencer" OR "fencing" OR "fencers" OR "fishing" OR "finswimming" OR "fistball" OR "floorball" OR "flying disc" OR "foosball" OR "futsal" OR "flickerball" OR "football" OR "frisbee" OR "gliding" OR "go" OR "gongfu" OR "gong fu" OR "goalball" OR "golf" OR "golfer" OR "golfers" OR "gymnast" OR "gymnasts" OR "gymnastics" OR "gymnastic" OR "gymkhanas" OR "half rubber" OR "highland games" OR "hap ki do" OR "halfrubber" OR "handball" OR "handballers" OR "handballer" OR "hapkido" OR "hiking" OR "hockey" OR "hsing-I" OR "hurling" OR "Hwa rang do" OR "hwarangdo" OR "horsemanship" OR "horseshoes" OR "orienteer" OR "orienteers" OR "orienteering" OR "iaido" OR "iceboating" OR "icestock" OR "intercrosse" OR "jousting" OR "jai alai" OR "jeet kune do" OR "jianzi" OR "jiu-jitsu" OR "jujutsu" OR "ju-jitsu" OR "kung fu" OR "kungfu" OR "kenpo" OR "judo" OR "judoka" OR "judoists" OR "judoist" OR "jump" OR "jumping" OR "jumper" OR "jian zi" OR "kabaddi" OR "kajukenbo" OR "karate" OR "karateists" OR "karateist" OR "karateka" OR "kayaking" OR "kendo" OR "kenjutsu" OR "kickball" OR "kickbox*" OR "kneeboarding" OR "krav maga" OR "kuk sool won" OR "kun-tao" OR "kuntao" OR "kyudo" OR "korfball" OR "lacrosse" OR "life saving" OR "lapta" OR "lawn tempest" OR "bowling" OR "bowls" OR "logrolling" OR "luge" OR "marathon" OR "marathons" OR "marathoning" OR "martial art" OR "martial arts" OR "martial artist" OR "martial artists" OR "motorsports" OR "mountainboarding" OR "mountain boarding" OR "mountaineer" OR "mountaineering" OR "mountaineers" OR "muay thai" OR "mallakhamb" OR "motorcross" OR "modern arnis" OR "naginata do" OR "netball" OR "ninepins" OR "nine-pins" OR "nordic combined" OR "nunchaku" OR "olympic*" OR "pes\u00e4pallo" OR "pitch and putt" OR "pool" OR "pato" OR "paddleball" OR "paddleboarding" OR "pankration" OR "pancratium" OR "parachuting" OR "paragliding" OR "paramotoring" OR "paraski" OR "paraskiing" OR "paraskier" OR "paraskier" OR "parakour" OR "pelota" OR "pencak silat" OR "pentathlon" OR "p\u00e9tanque" OR "petanque" OR "pickleball" OR "pilota" OR "pole bending" OR "pole vault" OR "polo" OR "polocrosse" OR "powerlifting" OR "player*" OR "powerboating" OR "pegging" OR "parathletic" OR "parathletics" OR "parasport*" OR "paraathletes" OR "paraathlete" OR "pushball" OR "push ball" OR "quidditch" OR "races" OR "race" OR "racing" OR "racewalking" OR "racewalker" OR "racewalkers" OR "rackets" OR "racketlon" OR "racquetball" OR "racquet" OR "racquets" OR "rafting" OR "regattas" OR "riding" OR "ringette" OR "rock-it-ball" OR "rogaining" OR "rock climbing" OR "roll ball" OR "roller derby" OR "roping" OR "rodeos" OR "rodeo" OR "riding" OR "rider" OR "riders" OR "rounders" OR "rowing" OR "rower" OR "rowers" OR "rug ball" OR "running" OR "runner" OR "runners" OR "rugby" OR "sailing" OR "san shou" OR "sepaktakraw" OR "sepak takraw" OR "san-jitsu" OR "savate" OR "shinty" OR "shishimai" OR "shooting" OR "singlestick" OR "single stick" OR "skateboarding" OR "skateboarder" OR "skateboarders" OR "skater" OR "skaters" OR "skating" OR "skipping" OR "racket game*" OR "rollerskating" OR "skelton" OR "skibobbing" OR "ski" OR "skiing" OR "skier" OR "skiers" OR "skydive" OR "skydiving" OR "skydivers" OR "skydiver" OR "skysurfing" OR "sledding" OR "sledging" OR "sled dog" OR "sleddog" OR "snooker" OR "sleighing" OR "snowboarder" OR "snowboarding" OR "snowboarders" OR "snowshoeing" OR "soccer" OR "softball" OR "spear fighting" OR "speed-a-way" OR "speedball" OR "sprint" OR "sprinting" OR "sprints" OR "squash" OR "stick fighting" OR "stickball" OR "stoolball" OR "stunt flying" OR "sumo" OR "surfing" OR "surfer" OR "surfers" OR "swimnastics" OR "swimming" OR "snowmobiling" OR "swim" OR "swimmer" OR "swimmers" OR "shot-put" OR "shot-putters" OR "shot-putter" OR "sport" OR "sports" OR "tae kwon do" OR "taekwondo" OR "taekgyeon" OR "taekkyeon" OR "taekkyon" OR "taekyun" OR "tang soo do" OR "tchoukball" OR "tennis" OR "tetherball" OR "throwing" OR "thrower" OR "throwers" OR "tai ji" OR "tai chi" OR "taiji" OR "t ai chi" OR "throwball" OR "tug of war" OR "tobogganing" OR "track and field" OR "track & field" OR "trampoline" OR "trampolining" OR "trampolinists" OR "trampolinist" OR "trapball" OR "trapshooting" OR "triathlon" OR "triathlete" OR "triathletes" OR "tubing" OR "tumbling" OR "vaulting" OR "volleyball" OR "wakeboarding" OR "wallyball" OR "weightlifting" OR "weightlifter" OR "weightlifters" OR "wiffle ball" OR "windsurfing" OR "windsurfer" OR "windsurfers" OR "walking" OR "wingwalking" OR "woodchopping" OR "wood chopping" OR "woodball" OR "wushu" OR "weight lifter" OR "weight lift" OR "weight lifters" OR "wrestling" OR "wrestler" OR "wrestlers" OR "vovinam" OR "vx" OR "yoga")\n3. #1 AND #2\n'

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
        "position": (-1, -1),
        "details": "",
    }


# Test case 3
def test_list_parser_case_3() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats")\n3. #1 AND not_a_ref_to_term_node\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    try:
        list_parser.parse()
    except ListQuerySyntaxError:
        pass
    assert list_parser.linter.messages[GENERAL_ERROR_POSITION][0] == {
        "code": "F1004",
        "is_fatal": True,
        "label": "invalid-token-sequence",
        "message": "The sequence of tokens is invalid.",
        "position": (3, 6),
        "details": "Last token of query item 3 must be a list item.",
    }


# Test case 4
def test_list_parser_case_4() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats")\n3. #1 AND #5\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    try:
        list_parser.parse()
    except ListQuerySyntaxError:
        pass

    assert list_parser.linter.messages[2][0] == {
        "code": "F3003",
        "is_fatal": True,
        "label": "invalid-list-reference",
        "message": "Invalid list reference in list query (not found)",
        "position": (7, 9),
        "details": "List reference #5 not found.",
    }
