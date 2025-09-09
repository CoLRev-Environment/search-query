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
       "search_string": "TS=(quantum dot)",
       "version": "1"
   }

Queries may optionally be stored in a generic or structured form:

.. code-block:: json

   {
       "platform": "wos",
       "search_string": "TS=(quantum dot)",
       "version": "1",
       "generic_query": "AND[quantum[TS=], dot[TS=]]"
   }
