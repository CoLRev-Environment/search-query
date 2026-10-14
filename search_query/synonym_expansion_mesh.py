"""Module for synonym expansion in search queries."""
from __future__ import annotations

import requests
from lxml import etree


def fetch_mesh_terms(term: str) -> list[str]:
    """Fetch MeSH descriptor IDs matching ``term``."""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "mesh", "term": term, "retmode": "xml"}

    response = requests.get(url, params=params, timeout=60)
    tree = etree.fromstring(response.content)

    mesh_ids = tree.xpath("//IdList/Id/text()")
    return mesh_ids


def fetch_mesh_synonyms(mesh_id: str) -> list[str]:
    """Fetch the descriptor terms associated with a MeSH ID."""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "mesh", "id": mesh_id, "retmode": "xml"}

    response = requests.get(url, params=params, timeout=60)
    tree = etree.fromstring(response.content)

    synonyms = tree.xpath("//Item[@Name='DS_MeshTerms']/Item/text()")
    return synonyms


def expand_query_with_synonyms(query: str) -> str:
    """Expand each AND-connected query term with its first MeSH descriptor."""
    terms = query.split(" AND ")
    expanded_terms = []

    for term in terms:
        mesh_ids = fetch_mesh_terms(term)
        if mesh_ids:
            synonyms = fetch_mesh_synonyms(mesh_ids[0])
            if synonyms:
                expanded_terms.append(f"({' OR '.join(synonyms)})")
            else:
                expanded_terms.append(term)
        else:
            expanded_terms.append(term)

    expanded_query = " AND ".join(expanded_terms)
    return expanded_query


if __name__ == "__main__":
    # Example usage
    QUERY = "asthma AND treatment"
    EXPANDED_QUERY = expand_query_with_synonyms(QUERY)
    print(EXPANDED_QUERY)
