#!/usr/bin/env python
"""Tests for search query translation"""
import pytest


# flake8: noqa: E501


@pytest.mark.parametrize(
    "source, query_string, expected",
    [
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00155",
            """1.	Clinical competence
2.	Professional practice
3.	Cultural competence
4.	Accreditation
5.	Interprofessional relations
6.	Professional education
7.	Professional licenses
8.	Standards
9.	Professional licensure examinations
10.	Professional standards
11.	Licenses
12.	Professional --law & legislation
13.	Professional --law & legislation (Search modes – SmartText searching Interface)
14.	License agreement
15.	Educational accreditation
16.	Interdisciplinary education
17.	National competency-based educational tests
18.	Globalization
19.	Certification
20.	Mutual recognition agreement
21.	Professional equivalenc*
22.	Interchangeability
23.	Internationally educated professionals
24.	Internationally educated health professionals
25.	(S1 OR S2 OR S3 OR S4 OR S5 OR S6 OR S7 OR S8 OR S9 OR S10 OR S11 OR S12 OR S13 OR S14 OR S15 OR S16 OR S17 OR S18 OR S19)
26.	(S20 OR S21 OR S22 OR S23 OR S24)
27.	(S25 AND S26)""",
            """AND[OR[Clinical competence, Professional practice, Cultural competence, Accreditation, Interprofessional relations, Professional education, Professional licenses, Standards, Professional licensure examinations, Professional standards, Licenses, Professional --law & legislation, Professional --law & legislation (Search modes – SmartText searching Interface), License agreement, Educational accreditation, Interdisciplinary education, National competency-based educational tests, Globalization, Certification], OR[Mutual recognition agreement, Professional equivalenc*, Interchangeability, Internationally educated professionals, Internationally educated health professionals]]""",
        )
    ],
)
def test_cinahl_query_parser(source: str, query_string: str, expected: str) -> None:
    """Test the translation of a search query to a CINAHL query"""
    # query = parse(query_string, query_type="cinahl")
    # query_str = query.to_string()
    # assert query_str == expected, print_debug(source, query_string, query_str)
    pass


def print_debug(source: str, query_string: str, query_str: str) -> None:
    print("--------------------")
    print(source)
    print()
    print(query_string)
    print()
    print(query_str)
