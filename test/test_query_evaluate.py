from search_query import AndQuery, OrQuery

def test_case1() -> None:

    records_dict = {
        "r1": {
            "title": "Microsourcing platforms for online labor",
            "colrev_status": "rev_included"
        },
        "r2": {
            "title": "Online work and the future of microsourcing",
            "colrev_status": "rev_included"
        },
        "r3": {
            "title": "Microsourcing case studies",
            "colrev_status": "rev_excluded"
        },
        "r4": {
            "title": "Freelancing and online job platforms",
            "colrev_status": "rev_excluded"
        },
    }

    query = AndQuery([
        OrQuery(["microsourcing"], search_field="ti"),
        OrQuery(["online"], search_field="ti")
    ], search_field="ti")

    result = query.evaluate(records_dict)

    assert result == {'total_evaluated': 4, 'selected': 2, 'true_positives': 2, 'false_positives': 0, 'false_negatives': 0, 'precision': 1.0, 'recall': 1.0, 'f1_score': 1.0}