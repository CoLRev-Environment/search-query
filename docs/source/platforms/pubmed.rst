
.. _pubmed:

PubMed
======

PubMed is a free resource supporting the search and retrieval of biomedical and life sciences literature.

Run a query
-----------

Queries can be entered using either:

- the `basic search box <https://pubmed.ncbi.nlm.nih.gov/>`_, or
- the `advanced Query builder <https://pubmed.ncbi.nlm.nih.gov/advanced/>`_.

These interfaces are functionally equivalent for the purposes of `search-query`. The full query string should always be **copied and stored** from either interface.

.. tip::

   Include field tags explicitly in the `search_string`. Leave the general `field` empty.

Store a query
-------------

When storing a PubMed query in a `.json` file or as a string:

- Use the content of the **Query box** or **Search details** section as the `search_string`.
- Leave the general `field` empty.

List query format
-----------------

PubMed allows combining previous searches using the search history panel. These list-based queries can reference earlier searches using numbered identifiers (e.g., `#1 OR #2`). In the advanced search interface, such combinations can also be created via the **“Add”** button. List queries are supported by `search-query` parsers.

List queries should be formatted as follows:

.. code-block:: json

   {
       "search_string": "1. dHealth[ti] OR telemedicine[ti]\n2. activity[ti] OR exercise[ti]\n3. #1 AND #2",
       "field": ""
   }

Best practices and recommendations
----------------------------------

The advanced PubMed interface offers a dropdown for search fields such as `[Title/Abstract]`, `[Author]`, etc. When using this feature:

- When the **same field** applies to the entire query, storing this value in the general `field` is safe.
- If the query contains **multiple search fields**, `search-query` will treat each term individually, and **leaving general `field` empty is preferred**.

.. note::

    PubMed performs **automatic term mapping** when queries are entered in the basic or advanced search boxes. For instance, a search for *eHealth* will also match related terms such as *telemedicine* and *electronic health*. This behavior should be kept in mind when reviewing search results or translating queries to other platforms, as the expanded concepts may not always be explicit in the query string.

Versions
--------

Latest version: **1**

No previous versions are documented.

Resources
---------

- `PubMed User Guide <https://pubmed.ncbi.nlm.nih.gov/help/>`_
- `Search Builder Help <https://pubmed.ncbi.nlm.nih.gov/advanced/>`_
