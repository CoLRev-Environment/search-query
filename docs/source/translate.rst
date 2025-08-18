.. _translate:

Translate
==========================================================

The ``translate`` functionality converts a search query written
for one platform into the correct syntax for another platform
This is useful when running the same query
across multiple literature databases (e.g., PubMed, Web of Science, or
EBSCO) without rewriting it manually.

In the example below, a query in PubMed syntax is first assigned to a
query_string variable. This string now needs to be parsed by calling the
``parse()`` function with the string and platform as the input. Using
``query.translate()``, it is converted into the Web of Science (``wos``)
format. The ``to_string()`` method then outputs the query in the proper
syntax for that platform.

.. code-block:: python
   :linenos:

   from search_query.parser import parse

   query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
   query = parse(query_string, platform="pubmed")
   wos_query = query.translate(target_syntax="wos")
   print(wos_query.to_string())
   # Output:
   # (AB="digital health" OR TI="digital health") AND (AB="privacy" OR TI="privacy")
