.. _ebsco:

EBSCOhost
=========

EBSCOhost provides access to a wide range of academic databases across disciplines, including business, education, psychology, and health sciences.

Run a query
-----------

EBSCOhost queries can be constructed using the standard `EBSCOhost advanced search interface <https://search.ebscohost.com/>`_ (requires institutional access).

When working with `search-query`, extract the **Search terms** from the **Search History** panel or persistent URL for use as the `search_string`.

EBSCOhost query syntax includes field tags such as `AB`, `TI`, `SU`, etc. These should be included directly in the `search_string`.

Store a query
-------------

When storing an EBSCOhost query in a `.json` file or as a string:

- Use the **Search History** or the **Search Terms** as the `search_string`.

.. tip::

   To ensure reproducibility, report the EBSCO database used (e.g., Business Source Complete) in the `database` field.

   Avoid setting a general `field` (available in `Advanced Search`) unless the entire query targets the same field (e.g., all terms limited to `AB` for Abstract). Mixed fields should keep general `field` empty.

   Do not use the **persistent link feature**.

List query format
-----------------

EBSCOhost supports building **multi-line queries** where individual components are defined as numbered search lines and later combined using references like ``S1 AND S2``. This method is often used in advanced or expert search modes.

List queries should be formatted as follows:

.. code-block:: json

   {
       "search_string": "1. TI (digital health OR telemedicine)\n2. AB (physical activity OR exercise)\n3. S1 AND S2",
       "field": ""
   }

Each numbered item defines a part of the query using EBSCOhost's field syntax. Later lines can combine them using boolean operators like ``AND``, ``OR``, or ``NOT``, allowing for structured, transparent query design.


Best practices and recommendations
----------------------------------

- **Use field tags** (e.g., `AB`, `TI`) explicitly in the query string.
- **Group nested queries** using parentheses to preserve logic.

Versions
--------

Latest version: **1**

No previous versions are documented.

Resources
---------

- `EBSCO Search Help <https://connect.ebsco.com/s/article/Searching-EBSCO-Databases?language=en_US>`_
- `EBSCO Search Fields Guide <https://connect.ebsco.com/s/article/Field-Codes-Searchable-EBSCOhost?language=en_US>`_
- `EBSCO wildcard restrictions <https://connect.ebsco.com/s/article/Searching-with-Wildcards-in-EDS-and-EBSCOhost?language=en_US>`_
