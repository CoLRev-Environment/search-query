#!/usr/bin/env python3
"""
Regression tests for commands shown in the JOSS paper.

These tests exist to ensure that the API demonstrated in the paper
continues to work as documented.
"""
from __future__ import annotations

import json

import pytest

# flake8: noqa: E501

# --- helpers ---------------------------------------------------------------


def _assert_parse_raises_with_codes(
    *, query: str, platform: str, codes: list[str]
) -> None:
    """
    Helper: assert parse() fails and reports expected error code(s) via
    excinfo.value.linter.messages (as used in the paper examples).
    """
    from search_query.parser import parse

    with pytest.raises(Exception) as excinfo:
        parse(query, platform=platform)

    raised_codes = [m["code"] for m in excinfo.value.linter.messages]

    missing = [c for c in codes if c not in raised_codes]
    assert not missing, (
        f"Expected code(s) {missing} not found.\n"
        f"Raised codes: {raised_codes}\n"
        f"Exception: {excinfo.value!r}"
    )


def _assert_parse_warns_with_codes_stdout(
    *, query: str, platform: str, codes: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    from search_query.parser import parse

    result = parse(query, platform=platform)
    out = capsys.readouterr().out

    for code in codes:
        assert code in out, f"Expected {code} in stdout:\n{out}"

    assert result is not None
    assert hasattr(result, "to_string")


# --- load options --------------------------------------------------------


def test_paper_option_1_parse_query_file(tmp_path: pytest.TempPathFactory) -> None:
    from search_query.search_file import load_search_file
    from search_query.parser import parse

    # create a minimal search-file.json (paper-style)
    payload = {
        "search_string": "digital AND work",
        "platform": "wos",
        "version": "1",
        "authors": [{"name": "Gerit Wagner"}],
        "record_info": {},
        "date": {},
    }
    p = tmp_path / "search-file.json"
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    search_file = load_search_file(str(p))
    wos_query = parse(search_file.search_string, platform=search_file.platform)

    assert wos_query is not None
    assert wos_query.to_string() == "digital AND work"


def test_paper_option_2_parse_query_string() -> None:
    from search_query.parser import parse

    wos_query = parse("digital AND work", platform="wos")
    assert wos_query is not None
    assert wos_query.to_string() == "digital AND work"


def test_paper_option_3_construct_programmatically() -> None:
    from search_query import OrQuery, AndQuery

    digital_synonyms = OrQuery(["digital", "virtual", "online"])
    work_synonyms = OrQuery(["work", "labor", "service"])
    query = AndQuery([digital_synonyms, work_synonyms], field="title")

    assert query is not None
    assert hasattr(query, "to_string")


def test_paper_option_4_load_query_from_database() -> None:
    from search_query.database import load_query

    ft50 = load_query("journals_FT50")
    assert (
        ft50.to_string()
        == 'SO=("Academy of Management Journal" OR "Academy of Management Review" OR "Accounting, Organizations and Society" OR "Administrative Science Quarterly" OR "American Economic Review" OR "Contemporary Accounting Research" OR "Econometrica" OR "Entrepreneurship Theory and Practice" OR "Harvard Business Review" OR "Human Relations" OR "Human Resource Management" OR "Information Systems Research" OR "Journal of Accounting and Economics" OR "Journal of Accounting Research" OR "Journal of Applied Psychology" OR "Journal of Business Ethics" OR "Journal of Business Venturing" OR "Journal of Consumer Psychology" OR "Journal of Consumer Research" OR "Journal of Finance" OR "Journal of Financial and Quantitative Analysis" OR "Journal of Financial Economics" OR "Journal of International Business Studies" OR "Journal of Management" OR "Journal of Management Information Systems" OR "Journal of Management Studies" OR "Journal of Marketing" OR "Journal of Marketing Research" OR "Journal of Operations Management" OR "Journal of Political Economy" OR "Journal of the Academy of Marketing Science" OR "Management Science" OR "Manufacturing and Service Operations Management" OR "Marketing Science" OR "MIS Quarterly" OR "Operations Research" OR "Organization Science" OR "Organization Studies" OR "Organizational Behavior and Human Decision Processes" OR "Production and Operations Management" OR "Quarterly Journal of Economics" OR "Research Policy" OR "Review of Accounting Studies" OR "Review of Economic Studies" OR "Review of Finance" OR "Review of Financial Studies" OR "Sloan Management Review" OR "Strategic Entrepreneurship Journal" OR "Strategic Management Journal" OR "The Accounting Review") OR IS=(0001-4273 OR 0363-7425 OR 0361-3682 OR 0001-8392 OR 0002-8282 OR 0823-9150 OR 0012-9682 OR 1042-2587 OR 0017-8012 OR 0018-7267 OR 0090-4848 OR 1047-7047 OR 0165-4101 OR 0021-8456 OR 0021-9010 OR 0167-4544 OR 0883-9026 OR 1057-7408 OR 0093-5301 OR 0022-1082 OR 0022-1090 OR 0304-405X OR 0047-2506 OR 0149-2063 OR 0742-1222 OR 0022-2429 OR 0022-2437 OR 0272-6963 OR 0022-3808 OR 0092-0703 OR 0025-1909 OR 1523-4614 OR 0732-2399 OR 0276-7783 OR 0030-364X OR 1047-7039 OR 0170-8406 OR 0749-5978 OR 1059-1478 OR 0033-5533 OR 0048-7333 OR 1380-6653 OR 0034-6527 OR 1572-3097 OR 0893-9454 OR 0036-8075 OR 1932-4391 OR 0143-2095 OR 0001-4826)'
    )
    assert ft50 is not None


# --- save SearchFile with load roundtrip --------------------------------


def test_paper_searchfile_save_roundtrip(tmp_path: pytest.TempPathFactory) -> None:
    from search_query import SearchFile
    from search_query.parser import parse
    from search_query.search_file import load_search_file

    pubmed_query = parse(
        '("dHealth"[Title/Abstract]) AND ("privacy"[Title/Abstract])',
        platform="pubmed",
    )

    search_file = SearchFile(
        query=pubmed_query,
        authors=[{"name": "Gerit Wagner"}],
        record_info={},
        date={},
    )

    p = tmp_path / "search-file.json"
    search_file.save(str(p))

    loaded = load_search_file(str(p))
    assert loaded.platform == "pubmed"
    assert isinstance(loaded.search_string, str)
    assert loaded.search_string


# --- linter messages ------------------------------------------


def test_paper_fatal_invalid_token_sequence_and_unbalanced_parentheses() -> None:
    _assert_parse_raises_with_codes(
        query="((digital[ti] OR virtual[ti]) AND AND work[ti]",
        platform="pubmed",
        codes=["PARSE_0004", "PARSE_0002"],
    )


def test_paper_warns_operator_precedence_pubmed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_parse_warns_with_codes_stdout(
        query="crowdwork[ti] or digital[ti] and work[ti]",
        platform="pubmed",
        codes=["STRUCT_0001", "STRUCT_0002"],
        capsys=capsys,
    )


def test_paper_fatal_invalid_year_token() -> None:
    _assert_parse_raises_with_codes(
        query="”crowdwork”[ti] AND 20122[pdat]",
        platform="pubmed",
        codes=["TERM_0001", "TERM_0002"],
    )


def test_paper_fatal_unsupported_field_ab() -> None:
    _assert_parse_raises_with_codes(
        query="crowdwork[ab]",
        platform="pubmed",
        codes=["FIELD_0001"],
    )


def test_paper_warns_wildcards_and_phrase_pubmed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_parse_warns_with_codes_stdout(
        query='AI*[tiab] OR "industry 4.0"[tiab]',
        platform="pubmed",
        codes=["PUBMED_0003", "PUBMED_0002"],
        capsys=capsys,
    )


def test_paper_warns_unbalanced_quote_or_bracket_pubmed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_parse_warns_with_codes_stdout(
        query='(digital[ti] OR online[ti]) OR "digital work"[ti]',
        platform="pubmed",
        codes=["QUALITY_0004", "QUALITY_0005"],
        capsys=capsys,
    )


# --- lint_file ------------------------------------------------------


def test_paper_lint_file_returns_messages() -> None:
    from search_query.linter import lint_file
    from search_query import SearchFile

    search_file = SearchFile(
        search_string="digital AND work",
        platform="wos",
        version="1",
        authors=[{"name": "Gerit Wagner"}],
        record_info={},
        date={},
    )
    messages = lint_file(search_file)
    assert messages is not None
    assert isinstance(messages, list)


# --- translate pubmed -> wos ---------------------------------------


def test_paper_translate_pubmed_to_wos_exact_string() -> None:
    from search_query.parser import parse

    query_string = '("dHealth"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
    pubmed_query = parse(query_string, platform="pubmed")
    wos_query = pubmed_query.translate(target_syntax="wos")
    assert (
        wos_query.to_string()
        == '(AB="dHealth" OR TI="dHealth") AND (AB="privacy" OR TI="privacy")'
    )
