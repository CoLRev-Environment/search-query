.. _load:

Load
====================

Queries can be loaded from strings/files, defined as objects, or retrieved from the internal database.

String/file
-------------------------

Search-query can parse queries from strings and JSON query files.
To load a JSON query file, run the parser:

.. code-block:: python

    from search_query.search_file import load_search_file
    from search_query.parser import parse

    search = load_search_file("search-file.json")
    query = parse(search.search_string, platform=search.platform)


JSON files in the standard format (Haddaway et al. 2022). Example:

.. code-block:: json

   {
      "record_info": {},
      "authors": [{"name": "Wagner, G.", "ORCID": "0000-0000-0000-1111"}],
      "date": {"data_entry": "2019.07.01", "search_conducted": "2019.07.01"},
      "platform": "Web of Science",
      "version": "1",
      "database": ["SCI-EXPANDED", "SSCI", "A&HCI"],
      "search_string": "TS=(quantum AND dot AND spin)"
   }


Query objects
-------------------------

Query objects can also be created programmatically.

.. code-block:: python

   from search_query import OrQuery, AndQuery

   # Typical building-blocks approach
   digital_synonyms = OrQuery(["digital", "virtual", "online"], field="abstract")
   work_synonyms = OrQuery(["work", "labor", "service"], field="abstract")
   query = AndQuery([digital_synonyms, work_synonyms])

Database
---------------------

Queries can be loaded from the internal database directly:

.. code-block:: python

   from search_query.database_queries import AIS_8

   print(AIS_8.to_string())
   # SO=("European Journal of Information Systems" OR "Information Systems Journal"
   # OR "Information Systems Research" OR "Journal of the Association for Information Systems"
   # OR "Journal of Information Technology" OR "Journal of Management Information Systems"
   # OR "Journal of Strategic Information Systems" OR "MIS Quarterly")
   # OR IS=(0960-085X OR 1476-9344 OR 1350-1917 OR 1365-2575 OR 1047-7047 OR 1526-5536
   # OR 1536-9323 OR 0268-3962 OR 1466-4437 OR 0742-1222 OR 1557-928X OR 0963-8687
   # OR 1873-1198 OR 0276-7783 OR 2162-9730)


It is also possible to load queries from the database using the `database` module:

.. code-block:: python

   from search_query.database import load_query

   FT50 = load_query("journals_FT50")

Once loaded, the query can be used as a building block for other queries:

.. code-block:: python

   # Combination with custom query blocks
   custom_block = ORQuery(....)
   full_query = ANDQuery(custom_block, AIS_8)

Links and references
--------------------------

- `bmi Search blocks <https://blocks.bmi-online.nl/>`_ (available under a creative-commons license)
- `SuRe: Search filters <https://sites.google.com/york.ac.uk/sureinfo/home/search-filters>`_
- `ISSG Search Filters Resource <https://sites.google.com/a/york.ac.uk/issg-search-filters-resource/home/https-sites-google-com-a-york-ac-uk-issg-search-filters-resource-collections-of-search-filters>`_

.. parsed-literal::

   Haddaway, N. R., Rethlefsen, M. L., Davies, M., Glanville, J., McGowan, B., Nyhan, K., & Young, S. (2022).
     A suggested data structure for transparent and repeatable reporting of bibliographic searching.
     *Campbell Systematic Reviews*, 18(4), e1288. doi: `10.1002/cl2.1288 <https://onlinelibrary.wiley.com/doi/full/10.1002/cl2.1288>`_
