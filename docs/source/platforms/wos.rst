.. _wos:

Web of Science
==============

Web of Science (WoS) is a multidisciplinary citation database that supports structured search queries with field tags and Boolean operators.

Run a Query
-----------

Queries in Web of Science can be constructed using:

- the `Basic search interface <https://www.webofscience.com/wos/woscc/basic-search>`_, or
- the `Advanced search interface <https://www.webofscience.com/wos/woscc/advanced-search>`_, which allows for precise control using field tags (e.g., `TI=`, `TS=`, `AU=`).

When working with `search-query`, we recommend copying the **Advanced search query string** directly for use as the `search_string`.

.. note::

   Web of Science supports structured queries using field tags such as `TS=` (Topic), `TI=` (Title), `AB=` (Abstract), `AU=` (Author), etc.

   You should include these tags explicitly in the `search_string`. Leave the `general_search_field` empty unless the entire query is uniformly scoped to a single field.

Store a Query
-------------

When storing a Web of Science query:

- Use the **Advanced search query string** as the `search_string`.
- Leave the `general_search_field` empty unless all terms share the same field tag.

Example::

   (TS="digital health") AND (TS="privacy")

Best Practices and Recommendations
----------------------------------

- Prefer **Advanced Search** for reproducible and structured queries.
- Use **explicit field tags** (`TS=`, `TI=`, `AB=`, etc.) instead of relying on default fields.


Resources
---------

- `Field Tags Reference <https://webofscience.help.clarivate.com/Content/wos-core-collection/woscc-search-field-tags.htm>`_
- `Web of Science Errors <https://images.webofknowledge.com/WOKRS528R6/help/TCT/ht_errors.html>`_

.. note::
    Field tags on `this page <https://images.webofknowledge.com/images/help/WOS/hs_wos_fieldtags.html>`_ are outdated (e.g., "DI" no longer works).
