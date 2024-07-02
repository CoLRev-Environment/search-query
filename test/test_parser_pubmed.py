#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.parser_pubmed import PubmedParser
from search_query.query import Query

# flake8: noqa: E501


@pytest.mark.parametrize(
    "source, query_string, expected",
    [
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00244",
            # """((Environment[Mesh:NoExp] OR "Environment health*"[tiab] OR "Environmental health*"[tiab] OR "planetary health*"[tiab] OR "planet health*"[tiab] OR "environmental issue*"[tiab] OR "environment issue*"[tiab] OR Ecolog*[tiab] OR "Carbon Footprint"[Mesh] OR "carbon footprint*"[tiab] OR Climate[Mesh:NoExp] OR Climat*[tiab] OR Ecosystem[Mesh:NoExp] OR Ecosystem*[tiab] OR Conservation*[tiab] OR "environment protection*"[tiab] OR "environmental protection*"[tiab] OR "environment remediation*"[tiab] OR "environmental remediation*"[tiab] OR "environment restoration*"[tiab] OR "environmental restoration*"[tiab] OR "sustainable develop*"[tiab] OR "environmental sustain*"[tiab] OR "environment sustain*"[tiab] OR Disasters[Mesh:NoExp] OR Disaster*[tiab] OR "Natural Disasters"[Mesh:NoExp] OR "Environmental Policy"[Mesh] OR "environmental polic*"[tiab] OR "environment polic*"[tiab] OR Environmentalism[Mesh] OR Environmentalism*[tiab] OR "Environmental Advocacy"[tiab] OR "Environmental Activism"[tiab] OR "Environmental justice"[tiab] OR "environment justice"[tiab] OR "environment awareness"[tiab] OR "environmental awareness"[tiab] OR "Energy-Generating Resources"[Mesh:NoExp] OR "energy generating resource*"[tiab] OR "Fossil Fuels"[Mesh:NoExp] OR "fossil fuel*"[tiab] OR "Natural Gas"[Mesh] OR "natural gas*"[tiab] OR "Renewable Energy"[Mesh:NoExp] OR "renewable energ*"[tiab] OR "sustainable energ*"[tiab] OR "Ecological and Environmental Phenomena"[Mesh:NoExp] OR "environmental phenomen*"[tiab] OR "Climate Change"[Mesh] OR "global warm*"[tiab] OR "Environmental Pollution"[Mesh:NoExp] OR Pollution*[tiab] OR "Air Pollution"[Mesh:NoExp] OR "Air Qualit*"[tiab] OR "Light Pollution"[Mesh] OR "Petroleum Pollution"[Mesh] OR "oil spill"[tiab] OR "Waste Products"[Mesh:NoExp] OR "waste product*"[tiab] OR "Water Pollution"[Mesh:NoExp] OR "acid rain"[tiab] OR "Environmental Health"[Mesh:NoExp] OR Ecotoxicology[Mesh] OR ecotoxicol*[tiab] OR "environmental toxic*"[tiab] OR "environment toxic*"[tiab] OR Sanitation[Mesh:NoExp] OR Sanitation[tiab] OR "Environmental Exposure"[Mesh:NoExp] OR "environmental exposure*"[tiab] OR "environment exposure*"[tiab] OR "Environmental Monitoring"[Mesh:NoExp] OR "environmental monitor*"[tiab] OR "environment monitor*"[tiab] OR "Environmental Biomarkers"[Mesh] OR "environmental biomarker*"[tiab] OR "Environmental Indicators"[Mesh] OR "environmental indicator*"[tiab] OR "environment indicator*"[tiab] OR "Water Quality"[Mesh] OR "water quality"[tiab] OR "sanitary survey*"[tiab] OR "Environmental Illness"[Mesh:NoExp] OR "environment illness*"[tiab] OR "environmental disease*"[tiab] OR "environmental illness*"[tiab] OR "environmental hypersensitivit*"[tiab]) AND (Literacy[Mesh] OR Literac*[tiab] OR Illiterac*[tiab] OR "Health Literacy"[Mesh] OR "Patient Education as Topic"[Mesh:NoExp] OR "patient education*"[tiab] OR "education of patient*"[tiab] OR "informal education*"[tiab] OR "Consumer Health Information"[Mesh:NoExp] OR "consumer health*"[tiab] OR "Health Knowledge, Attitudes, Practice"[Mesh] OR "health knowledge*"[tiab] OR "Health Communication"[Mesh] OR "health communication*"[tiab] OR "community-based participatory research"[Mesh] OR "participatory research*"[tiab] OR "citizen science*"[tiab]))""",
            """(Environment[Mesh:NoExp] OR "Environment health*"[tiab]) AND (Literacy[Mesh] OR Literac*[tiab])""",
            """AND[OR[Environment[mesh_no_exp], Environment health*[tiab]], OR[Literacy[mesh], Literac*[tiab]]]""",
        )
    ],
)
def test_pubmed_query_parser(source: str, query_string: str, expected: str) -> None:
    """Test the translation of a search query to a Pubmed query"""

    parser = PubmedParser(query_string)
    query = parser.parse()
    query_str = query.to_string()

    assert query_str == expected, print_debug(  # type: ignore
        parser, query, source, query_string, query_str
    )


def print_debug(
    parser: PubmedParser, query: Query, source: str, query_string: str, query_str: str
) -> None:
    print("--------------------")
    # print(source)
    # print()
    print(query_string)
    print()
    # parser.parse_list()
    print()
    print(parser.get_token_types(parser.tokens))
    print(query_str)
    print(query.to_string("structured"))
