.. _save:

Save
==========================================================

To write a query to a JSON file, run the serializer:

.. code-block:: python

    from search_query import SearchFile
    from search_query.and_query import AndQuery

    query = AndQuery(["digital", "work"], field="title")

    search_file = SearchFile(
        filename="search-file.json",
        query_str=query.to_string(platform="wos"),
        platform="wos",
        authors=[{"name": "Tom Brady"}],
        record_info={},
        date={}
    )

    search_file.save()
