search\_query.query
===================

The query classes implement a **generic intermediate representation (IR)**
that abstracts away platform-specific syntax. Parsers from any platform
produce the same tree of logical operators and terms, enabling
cross-platform translation and version upgrades.

Example round-trip:

.. code-block:: python

   from search_query.parser import parse

   q_wos = parse('TS=("digital health")', platform='wos')
   ir = q_wos.translate(target_syntax='generic')
   q_back = ir.translate(target_syntax='wos')

.. automodule:: search_query.query

   .. rubric:: Classes

   .. autosummary::

      Query
      SearchField
      Term

