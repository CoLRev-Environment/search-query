.. _save:

Save
==========================================================

To write a query to a JSON file, run the serializer:

.. code-block:: python

    from search_query import SearchFile
    from search_query.query_and import AndQuery

    query = AndQuery(["digital", "work"], field="title")
    query.translate("wos")

    search_file = SearchFile(
        search_string=query.to_string(),
        platform="wos",
        version="1",
        authors=[{"name": "Tom Brady"}],
        record_info={},
        date={}
    )

    search_file.save("search-file.json")

Saved search strings include a ``version`` field so they can be
re-parsed with the exact syntax they were created with:

.. code-block:: json

    {
        "search_string": "AND[title][digital[title], work[title]]",
        "platform": "wos",
        "authors": [
            {
                "name": "Tom Brady"
            }
        ],
        "record_info": {},
        "date": {},
        "field": "",
        "version": "1"
    }

Queries may optionally be stored in a generic form:

.. code-block:: python

    from search_query.parser import parse

    query_string = 'digital[ti] AND work[ti]'
    pubmed_query = parse(query_string, platform="pubmed")

    generic_query = pubmed_query.translate(target_syntax="generic")
    generic_query_str = generic_query.to_generic_string()
    # AND[digital[title], work[title]]

    search_file = SearchFile(
        search_string=pubmed_query.to_string(),
        platform="pubmed",
        version="1",
        generic_query=generic_query_str
    )
    search_file.save("search-file.json")

.. code-block:: json

    {
        "search_string": "digital[ti] AND work[ti]",
        "platform": "pubmed",
        "authors": [],
        "record_info": {},
        "date": {},
        "field": "",
        "version": "1",
        "generic_query": "AND[digital[title], work[title]]"
    }
