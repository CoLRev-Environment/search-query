.. _translate:

Translate
==========================================================

TODO

.. code-block:: python
   :linenos:

   from search_query.parser import parse


   query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
   query = parse(query_string, platform="pubmed")
   wos_query = query.translate(target_syntax="wos")
