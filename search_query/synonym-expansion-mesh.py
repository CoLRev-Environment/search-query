import requests
from lxml import etree


def fetch_mesh_terms(term):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "mesh", "term": term, "retmode": "xml"}

    response = requests.get(url, params=params)
    tree = etree.fromstring(response.content)

    mesh_ids = tree.xpath("//IdList/Id/text()")
    return mesh_ids


def fetch_mesh_synonyms(mesh_id):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "mesh", "id": mesh_id, "retmode": "xml"}

    response = requests.get(url, params=params)
    tree = etree.fromstring(response.content)

    synonyms = tree.xpath("//Item[@Name='DS_MeshTerms']/Item/text()")
    return synonyms


def expand_query_with_synonyms(query):
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


# Example usage
query = "asthma AND treatment"
expanded_query = expand_query_with_synonyms(query)
print(expanded_query)
