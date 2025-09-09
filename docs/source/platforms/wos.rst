.. _wos:

Web of Science
==============

Web of Science (WoS) is a multidisciplinary citation database that supports structured search queries with field tags and Boolean operators.

Run a query
-----------

Queries in Web of Science can be constructed using:

- the `Basic search interface <https://www.webofscience.com/wos/woscc/basic-search>`_, or
- the `Advanced search interface <https://www.webofscience.com/wos/woscc/advanced-search>`_, which allows for precise control using field tags (e.g., `TI=`, `TS=`, `AU=`).

When working with `search-query`, the **Advanced search query string** should be copied directly for use as the `search_string`.

Web of Science supports structured queries using field tags such as `TS=` (Topic), `TI=` (Title), `AB=` (Abstract), `AU=` (Author), etc.

.. tip::

   Include field tags explicitly in the `search_string`. Leave the general `field` empty.

Store a query
-------------

When storing a Web of Science query:

- Use the **Advanced search query string** as the `search_string`.
- Leave the general `field` empty unless all terms share the same field tag.

Example::

   (TS="digital health") AND (TS="privacy")


List query format
-----------------

Web of Science allows the construction of **complex queries** by combining previously defined search sets using numbered references (e.g., ``#1 AND #2``). This list-based approach is commonly used in systematic searches where multiple search lines are logically combined.

Such list queries are supported by the ``search-query`` parsers and allow referencing earlier statements using ``#`` followed by the search line number.

List queries should be formatted as follows:

.. code-block:: json

   {
       "search_string": "1. TS=(digital health OR telemedicine)\n2. TS=(physical activity OR exercise)\n3. #1 AND #2",
       "field": ""
   }

Each numbered line represents an individual query component, and later lines can combine previous results using logical operators like ``AND``, ``OR``, or ``NOT``.

Best practices and recommendations
----------------------------------

- Prefer **Advanced Search** for reproducible and structured queries.
- Use **explicit field tags** (`TS=`, `TI=`, `AB=`, etc.) instead of relying on default fields.

Versions
--------

Latest version: **1**

Deprecated versions:

- **0**: Initial version with basic support for Web of Science queries. Field tags on
  `this page <https://images.webofknowledge.com/images/help/WOS/hs_wos_fieldtags.html>`_
  are outdated (e.g., "DI" no longer works). The page is no longer available, but can be
  accessed through the Wayback Machine.

Resources
---------

- `Field Tags Reference <https://webofscience.help.clarivate.com/Content/wos-core-collection/woscc-field-tags.htm>`_
- `Web of Science Errors <https://images.webofknowledge.com/WOKRS528R6/help/TCT/ht_errors.html>`_
