.. _load:

Load
====================

Queries can be loaded from strings/files, defined as objects, or retrieved from the internal database.

String/File
-------------------------

Search-query can parse queries from strings and JSON query files.
To load a JSON query file, run the parser:

.. code-block:: python

    from search_query.search_file import SearchFile
    from search_query.parser import parse

    search = SearchFile("search-file.json")
    query = parse(search.search_string, platform=search.platform)


JSON files in the standard format (Haddaway et al. 2022). Example:

.. code-block:: json

   {
      "record_info": {},
      "authors": [{"name": "Wagner, G.", "ORCID": "0000-0000-0000-1111"}],
      "date": {"data_entry": "2019.07.01", "search_conducted": "2019.07.01"},
      "platform": "Web of Science",
      "database": ["SCI-EXPANDED", "SSCI", "A&HCI"],
      "search_string": "TS=(quantum AND dot AND spin)"
   }


Query objects
-------------------------

Query objects can also be created programmatically.

.. code-block:: python

   from search_query import OrQuery, AndQuery

   # Typical building-blocks approach
   digital_synonyms = OrQuery(["digital", "virtual", "online"], search_field="Abstract")
   work_synonyms = OrQuery(["work", "labor", "service"], search_field="Abstract")
   query = AndQuery([digital_synonyms, work_synonyms], search_field="Author Keywords")

Database
---------------------

.. code-block:: python

   from search-query import database

   query = database.load_query("journals_FT50")



.. code-block:: python

   from search_query.database import FT50, clinical_trials

   print(FT50)
   > OR[issn=1234, issn=5678, JN="MIS Quartery", ...]

   print(clinical_trials)
   > OR[title=rct, title="clinical trial", title="randomized controlled trial", title="experiment", ...]

   # Combination with custom query blocks
   custom_block = ORQuery(....)
   full_query = ANDQuery(custom_block, clinical_trials, FT50)

In addition, the ``database_queries`` offer direct programmatic access to full queries and filters:

.. code-block:: python

   from search_query.database_queries import FT50

   print(FT50)


Links:

- `search blocks <https://blocks.bmi-online.nl/>`_ are available under a creative-commons license
- `overview_1 <https://sites.google.com/york.ac.uk/sureinfo/home/search-filters>`_
- `overview_2 <https://sites.google.com/a/york.ac.uk/issg-search-filters-resource/home/https-sites-google-com-a-york-ac-uk-issg-search-filters-resource-collections-of-search-filters>`_

References
----------------

.. parsed-literal::

   Haddaway, N. R., Rethlefsen, M. L., Davies, M., Glanville, J., McGowan, B., Nyhan, K., & Young, S. (2022).
     A suggested data structure for transparent and repeatable reporting of bibliographic searching.
     *Campbell Systematic Reviews*, 18(4), e1288. doi: `10.1002/cl2.1288 <https://onlinelibrary.wiley.com/doi/full/10.1002/cl2.1288>`_
