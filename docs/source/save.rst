.. _save:

Save
==========================================================

To write a query to a JSON file, run the serializer:

.. code-block:: python

    from search_query import save_file

    save_file(
        filename="search-file.json",
        query_str=query.to_string(syntax="wos"),
        syntax="wos",
        authors=[{"name": "Tom Brady"}],
        record_info={},
        date={}
    )
