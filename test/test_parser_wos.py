#!/usr/bin/env python
"""Tests for search query translation"""
import json
from pathlib import Path

import pytest

from search_query.parser import WOSListParser
from search_query.parser import WOSParser
from search_query.query import Query

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, tokens",
    [
        (
            "AB=(Health)",
            [("AB=", (0, 3)), ("(", (3, 4)), ("Health", (4, 10)), (")", (10, 11))],
        ),
        ("AB=Health", [("AB=", (0, 3)), ("Health", (3, 9))]),
        ("Health", [("Health", (0, 6))]),
        ("(Health*)", [("(", (0, 1)), ("Health*", (1, 8)), (")", (8, 9))]),
        (
            "(Health NOT Care*)",
            [
                ("(", (0, 1)),
                ("Health", (1, 7)),
                ("NOT", (8, 11)),
                ("Care*", (12, 17)),
                (")", (17, 18)),
            ],
        ),
        (
            """TI=(((morphine NEAR/2 equ*) or MME)) OR AB=(((morphine NEAR/2 equ*) or MME))""",
            [
                ("TI=", (0, 3)),
                ("(", (3, 4)),
                ("(", (4, 5)),
                ("(", (5, 6)),
                ("morphine", (6, 14)),
                ("NEAR/2", (15, 21)),
                ("equ*", (22, 26)),
                (")", (26, 27)),
                ("or", (28, 30)),
                ("MME", (31, 34)),
                (")", (34, 35)),
                (")", (35, 36)),
                ("OR", (37, 39)),
                ("AB=", (40, 43)),
                ("(", (43, 44)),
                ("(", (44, 45)),
                ("(", (45, 46)),
                ("morphine", (46, 54)),
                ("NEAR/2", (55, 61)),
                ("equ*", (62, 66)),
                (")", (66, 67)),
                ("or", (68, 70)),
                ("MME", (71, 74)),
                (")", (74, 75)),
                (")", (75, 76)),
            ],
        ),
        (
            """TS=((narcotic-free or narcoticfree or narcotic-sparing or narcoticsparing or non-opioid or nonopioid or non-opiate or nonopiate or opioid-free or opioidfree or OFA or opiate-based or opiatebased or opioid-based or opioidbased or OBA or opioid-less or opioidless or opiate-less or opiateless or opioid-reduced or opiate-reduced or opiate-free or opiatefree or opioid-sparing or opioidsparing or opiate-sparing or opiatesparing or opioid management or opiate management))""",
            [
                ("TS=", (0, 3)),
                ("(", (3, 4)),
                ("(", (4, 5)),
                ("narcotic-free", (5, 18)),
                ("or", (19, 21)),
                ("narcoticfree", (22, 34)),
                ("or", (35, 37)),
                ("narcotic-sparing", (38, 54)),
                ("or", (55, 57)),
                ("narcoticsparing", (58, 73)),
                ("or", (74, 76)),
                ("non-opioid", (77, 87)),
                ("or", (88, 90)),
                ("nonopioid", (91, 100)),
                ("or", (101, 103)),
                ("non-opiate", (104, 114)),
                ("or", (115, 117)),
                ("nonopiate", (118, 127)),
                ("or", (128, 130)),
                ("opioid-free", (131, 142)),
                ("or", (143, 145)),
                ("opioidfree", (146, 156)),
                ("or", (157, 159)),
                ("OFA", (160, 163)),
                ("or", (164, 166)),
                ("opiate-based", (167, 179)),
                ("or", (180, 182)),
                ("opiatebased", (183, 194)),
                ("or", (195, 197)),
                ("opioid-based", (198, 210)),
                ("or", (211, 213)),
                ("opioidbased", (214, 225)),
                ("or", (226, 228)),
                ("OBA", (229, 232)),
                ("or", (233, 235)),
                ("opioid-less", (236, 247)),
                ("or", (248, 250)),
                ("opioidless", (251, 261)),
                ("or", (262, 264)),
                ("opiate-less", (265, 276)),
                ("or", (277, 279)),
                ("opiateless", (280, 290)),
                ("or", (291, 293)),
                ("opioid-reduced", (294, 308)),
                ("or", (309, 311)),
                ("opiate-reduced", (312, 326)),
                ("or", (327, 329)),
                ("opiate-free", (330, 341)),
                ("or", (342, 344)),
                ("opiatefree", (345, 355)),
                ("or", (356, 358)),
                ("opioid-sparing", (359, 373)),
                ("or", (374, 376)),
                ("opioidsparing", (377, 390)),
                ("or", (391, 393)),
                ("opiate-sparing", (394, 408)),
                ("or", (409, 411)),
                ("opiatesparing", (412, 425)),
                ("or", (426, 428)),
                ("opioid management", (429, 446)),
                ("or", (447, 449)),
                ("opiate management", (450, 467)),
                (")", (467, 468)),
                (")", (468, 469)),
            ],
        ),
        (
            """TS=((((multimodal$ or multi-modal$ or unimodal$ or uni-modal$ or conventional) NEAR/1 (an$esthe* or analge* or approach or strategy or strategies or protocol$ or regimen$)) or MITA or ((combination or combined) NEAR/1 (infusion* or injection*))))""",
            [
                ("TS=", (0, 3)),
                ("(", (3, 4)),
                ("(", (4, 5)),
                ("(", (5, 6)),
                ("(", (6, 7)),
                ("multimodal$", (7, 18)),
                ("or", (19, 21)),
                ("multi-modal$", (22, 34)),
                ("or", (35, 37)),
                ("unimodal$", (38, 47)),
                ("or", (48, 50)),
                ("uni-modal$", (51, 61)),
                ("or", (62, 64)),
                ("conventional", (65, 77)),
                (")", (77, 78)),
                ("NEAR/1", (79, 85)),
                ("(", (86, 87)),
                ("an$esthe*", (87, 96)),
                ("or", (97, 99)),
                ("analge*", (100, 107)),
                ("or", (108, 110)),
                ("approach", (111, 119)),
                ("or", (120, 122)),
                ("strategy", (123, 131)),
                ("or", (132, 134)),
                ("strategies", (135, 145)),
                ("or", (146, 148)),
                ("protocol$", (149, 158)),
                ("or", (159, 161)),
                ("regimen$", (162, 170)),
                (")", (170, 171)),
                (")", (171, 172)),
                ("or", (173, 175)),
                ("MITA", (176, 180)),
                ("or", (181, 183)),
                ("(", (184, 185)),
                ("(", (185, 186)),
                ("combination", (186, 197)),
                ("or", (198, 200)),
                ("combined", (201, 209)),
                (")", (209, 210)),
                ("NEAR/1", (211, 217)),
                ("(", (218, 219)),
                ("infusion*", (219, 228)),
                ("or", (229, 231)),
                ("injection*", (232, 242)),
                (")", (242, 243)),
                (")", (243, 244)),
                (")", (244, 245)),
                (")", (245, 246)),
            ],
        ),
        ("ne?t", [("ne?t", (0, 4))]),
    ],
)
def test_tokenization_wos(query_string: str, tokens: tuple) -> None:
    print(query_string)
    print()
    wos_parser = WOSParser(query_string)
    wos_parser.tokenize()
    print(wos_parser.tokens)
    print(wos_parser.get_token_types(wos_parser.tokens, legend=True))
    print(tokens)
    assert wos_parser.tokens == tokens


@pytest.mark.parametrize(
    "node_content, expected_type",
    [
        ("#6 AND PY=(2000-2022)", "AND_node"),
    ],
)
def test_wos_node_content(node_content: str, expected_type: str) -> None:
    """Test the content type of a node"""

    parser = WOSListParser(node_content)

    if expected_type == "AND_node":
        assert parser.is_and_node(node_content)


directory_path = Path("data/wos")
file_list = list(directory_path.glob("*.json"))


# Use the list of files with pytest.mark.parametrize
@pytest.mark.parametrize("file_path", file_list)
def test_wos_query_parser(file_path: str) -> None:
    """Test the translation of a search query to a WOS query"""

    with open(file_path) as file:
        data = json.load(file)
        source = file_path
        # TODO : use SearchHistoryFile to validate
        query_string = data["search_string"]
        expected = data["parsed"]["search"]

        parser = WOSParser(query_string)
        query = parser.parse()
        query_str = query.to_string()
        assert query_str == expected, print_debug(  # type: ignore
            parser, query, source, query_string, query_str
        )


def print_debug_list(
    parser: WOSListParser, query: Query, source: str, query_string: str, query_str: str
) -> None:
    print("--------------------")
    # print(source)
    # print()
    print(query_string)
    print()
    parser.parse_list()
    print()
    print(parser.get_token_types(parser.tokens))
    print(query_str)
    print(query.to_string("structured"))


def print_debug(
    parser: WOSParser, query: Query, source: str, query_string: str, query_str: str
) -> None:
    print("--------------------")
    # print(source)
    # print()
    print(query_string)
    print()
    print(parser.get_token_types(parser.tokens))
    print(query_str)
    print(query.to_string("structured"))
