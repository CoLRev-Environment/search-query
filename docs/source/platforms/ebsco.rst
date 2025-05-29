.. _ebsco:

EBSCOHost
=========

EBSCOHost provides access to a wide range of academic databases across disciplines, including business, education, psychology, and health sciences.

Run a Query
-----------

EBSCOHost queries can be constructed using:

- the standard `EBSCOHost advanced search interface <https://search.ebscohost.com/>`_ (requires institutional access), or
- the **persistent link feature**, which captures the full query string for reproducibility.

When working with `search-query`, we recommend extracting the **Search terms** from the **Search History** panel or persistent URL for use as the `search_string`.

.. note::

   EBSCOHost query syntax includes field tags such as `AB`, `TI`, `SU`, etc. These should be included directly in the `search_string`.

   Avoid setting a `general_search_field` unless the entire query targets the same field (e.g., all terms limited to `AB` for Abstract). Mixed fields should keep `general_search_field` empty.

Store a Query
-------------

When storing an EBSCOHost query in a `.json` file or as a string:

- Use the **Search History** or the **Search Terms** as the `search_string`.
- Leave the `general_search_field` empty **unless** the same field is used consistently across all terms.

.. tip::

   To ensure reproducibility, consider including the EBSCO database used (e.g., Business Source Complete) in the `database` field.

Best Practices and Recommendations
----------------------------------

- **Use field tags** (e.g., `AB`, `TI`) explicitly in the query string.
- **Group nexted queries** using parentheses to preserve logic.

Resources
---------

- `EBSCO Search Help <https://connect.ebsco.com/s/article/Searching-EBSCO-Databases?language=en_US>`_
- `EBSCO Search Fields Guide <https://connect.ebsco.com/s/article/Field-Codes-Searchable-EBSCOhost?language=en_US>`_
- `EBSCO wildcard restrictions <https://connect.ebsco.com/s/article/Searching-with-Wildcards-in-EDS-and-EBSCOhost?language=en_US>`_
