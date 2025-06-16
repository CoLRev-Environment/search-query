
.. _pubmed:

PubMed
======

PubMed is a free resource supporting the search and retrieval of biomedical and life sciences literature.

Run a Query
-----------

Queries can be entered using either:

- the `basic search box <https://pubmed.ncbi.nlm.nih.gov/>`_, or
- the `advanced Query builder <https://pubmed.ncbi.nlm.nih.gov/advanced/>`_.

These interfaces are functionally equivalent for the purposes of `search-query`. We recommend users always **copy and store the full query string** from either interface.

.. note::

   For parsing PubMed queries, we recommend using the queries entered in the basic or advanced box as the *search_string* and leave the *general_search_field* empty.

   When running the same query with different serach fields, as in this `example <https://www.cabidigitallibrary.org/doi/10.1079/SEARCHRXIV.2023.00236>`_, *search-query* will assume that the queries are added with an "OR" operator.

Store a Query
-------------

When storing a PubMed query in a `.json` file or as a string:

- Use the content of the **Query box** or **Search details** section as the `search_string`.
- Leave the `general_search_field` empty.

List Query Format
--------------------

PubMed allows users to **combine previous searches** using the search history panel. These list-based queries can reference earlier searches using numbered identifiers (e.g., `#1 OR #2`). In the advanced search interface, such combinations can also be created via the **“Add”** button. List queries are supported by `search-query` parsers.

Best Practices and Recommendations
----------------------------------

The advanced PubMed interface offers a dropdown for search fields such as `[Title/Abstract]`, `[Author]`, etc. When using this feature:

- If you apply the **same field** to the entire query, it is safe to store this value in the `general_search_field`.
- If the query contains **multiple search fields**, `search-query` will treat each term individually, and **leaving `general_search_field` empty is preferred**.

.. note::

   PubMed performs **automatic term mapping** when queries are entered in the basic or advanced search boxes. For instance, a search for *eHealth* will also match related terms such as *telemedicine* and *electronic health*. This behavior should be kept in mind when reviewing search results or translating queries to other platforms, as the expanded concepts may not always be explicit in the query string.

Resources
---------

- `PubMed User Guide <https://pubmed.ncbi.nlm.nih.gov/help/>`_
- `Search Builder Help <https://pubmed.ncbi.nlm.nih.gov/advanced/>`_
