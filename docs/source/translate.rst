.. _translate:

Translate
==========================================================

..
   TODO
   also desribe how to translate to list format (flag/option for to-string methods)

.. code-block:: python
   :linenos:

   from search_query.parser import parse


   query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
   query = parse(query_string, platform="pubmed")
   wos_query = query.translate(target_syntax="wos")
