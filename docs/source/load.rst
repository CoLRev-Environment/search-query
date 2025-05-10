.. _load:

Load
====================

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

Query objects can also be created programmatically.

Filters (TODO)
---------------------

- `search blocks <https://blocks.bmi-online.nl/>`_ are available under a creative-commons license
- `overview_1 <https://sites.google.com/york.ac.uk/sureinfo/home/search-filters>`_
- `overview_2 <https://sites.google.com/a/york.ac.uk/issg-search-filters-resource/home/https-sites-google-com-a-york-ac-uk-issg-search-filters-resource-collections-of-search-filters>`_

References
----------------

.. parsed-literal::

   Haddaway, N. R., Rethlefsen, M. L., Davies, M., Glanville, J., McGowan, B., Nyhan, K., & Young, S. (2022).
     A suggested data structure for transparent and repeatable reporting of bibliographic searching.
     *Campbell Systematic Reviews*, 18(4), e1288. doi: `10.1002/cl2.1288 <https://onlinelibrary.wiley.com/doi/full/10.1002/cl2.1288>`_
