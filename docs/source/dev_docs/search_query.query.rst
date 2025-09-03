search\_query.query
===================

The query classes implement a **generic query** as an intermediate representation (IR)
that abstracts away platform-specific syntax. Parsers from any platform
produce the same tree of logical operators and terms, enabling
cross-platform translation and version upgrades.

Example round-trip:

.. code-block:: python

   from search_query.parser import parse

   query_wos = parse('TS=("digital health")', platform='wos')
   query_generic = query_wos.translate(target_syntax='generic')
   query_back = query_generic.translate(target_syntax='wos')

.. automodule:: search_query.query

   .. rubric:: Classes

   .. autosummary::

      Query
      SearchField
      Term
