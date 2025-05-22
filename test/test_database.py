#!/usr/bin/env python
"""Tests for search query database."""
import pytest

from search_query.database import list_queries
from search_query.database import list_queries_with_details
from search_query.database import load_query
from search_query.query import Query

# ruff: noqa: E501
# flake8: noqa: E501


def test_load_query_journals_ft50() -> None:
    """Test loading the JOURNALS_FT50 query file."""
    query = load_query("journals_FT50")

    assert isinstance(query, Query)
    print(query.to_generic_string())
    assert (
        query.to_generic_string()
        == 'OR[OR[SO=]["Academy of Management Journal", "Academy of Management Review", "Accounting, Organizations and Society", "Administrative Science Quarterly", "American Economic Review", "Contemporary Accounting Research", "Econometrica", "Entrepreneurship Theory and Practice", "Harvard Business Review", "Human Relations", "Human Resource Management", "Information Systems Research", "Journal of Accounting and Economics", "Journal of Accounting Research", "Journal of Applied Psychology", "Journal of Business Ethics", "Journal of Business Venturing", "Journal of Consumer Psychology", "Journal of Consumer Research", "Journal of Finance", "Journal of Financial and Quantitative Analysis", "Journal of Financial Economics", "Journal of International Business Studies", "Journal of Management", "Journal of Management Information Systems", "Journal of Management Studies", "Journal of Marketing", "Journal of Marketing Research", "Journal of Operations Management", "Journal of Political Economy", "Journal of the Academy of Marketing Science", "Management Science", "Manufacturing and Service Operations Management", "Marketing Science", "MIS Quarterly", "Operations Research", "Organization Science", "Organization Studies", "Organizational Behavior and Human Decision Processes", "Production and Operations Management", "Quarterly Journal of Economics", "Research Policy", "Review of Accounting Studies", "Review of Economic Studies", "Review of Finance", "Review of Financial Studies", "Sloan Management Review", "Strategic Entrepreneurship Journal", "Strategic Management Journal", "The Accounting Review"], OR[IS=][0001-4273, 0363-7425, 0361-3682, 0001-8392, 0002-8282, 0823-9150, 0012-9682, 1042-2587, 0017-8012, 0018-7267, 0090-4848, 1047-7047, 0165-4101, 0021-8456, 0021-9010, 0167-4544, 0883-9026, 1057-7408, 0093-5301, 0022-1082, 0022-1090, 0304-405X, 0047-2506, 0149-2063, 0742-1222, 0022-2429, 0022-2437, 0272-6963, 0022-3808, 0092-0703, 0025-1909, 1523-4614, 0732-2399, 0276-7783, 0030-364X, 1047-7039, 0170-8406, 0749-5978, 1059-1478, 0033-5533, 0048-7333, 1380-6653, 0034-6527, 1572-3097, 0893-9454, 0036-8075, 1932-4391, 0143-2095, 0001-4826]]'
    )

    # expect FileNotFoundError if the file does not exist
    with pytest.raises(KeyError):
        load_query("non_existent_query")


def test_list_queries_with_details() -> None:
    """Test listing queries with details."""
    queries = list_queries_with_details()

    assert isinstance(queries, dict)
    assert len(queries) > 0
    assert "journals_FT50" in queries


def test_list_queries() -> None:
    """Test listing queries."""
    list_of_queries = list_queries()

    assert "ais_senior_scholars_basket" in list_of_queries
