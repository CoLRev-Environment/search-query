.. _save:

Save
==========================================================

To write a query to a JSON file, run the serializer:

.. code-block:: python

    from search_query import SearchFile
    from search_query.and_query import AndQuery

    query = AndQuery(["digital", "work"], field="title")
    query.translate("wos")

    search_file = SearchFile(
        filename="search-file.json",
        query_str=query.to_string(),
        platform="wos",
        version="1",
        authors=[{"name": "Tom Brady"}],
        record_info={},
        date={}
    )

    search_file.save()

Backward compatibility
----------------------

Saved search strings include a ``version`` field so they can be
re-parsed with the exact syntax they were created with:

.. code-block:: json

   {
       "platform": "wos",
       "search_string": "TS=(digital AND work)",
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
        filename="search-file.json",
        query_str=pubmed_query.to_string(),
        platform="pubmed",
        version="1",
        generic_query=generic_query_str
    )

.. code-block:: json

   {
       "platform": "wos",
       "search_string": "TS=(digital AND work)",
       "version": "1",
       "generic_query": "AND[digital[title], work[title]]"
   }
