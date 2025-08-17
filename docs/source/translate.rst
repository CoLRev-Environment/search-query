.. _translate:

Translate
==========================================================

The translate function translates a query from one database syntax to another. 
Supported syntaxes are: Web of Science, PubMed, EBSCO and a generic syntax.
If the syntax of the given query, or the requested target syntax, is from an unknown platform, the function will raise an exception.
The output of the translate function is a query object.
Additionally, using the to_string() function, the query object can be transformed to a string, ready to be used on the according platform. 


..
   TODO
   also describe how to translate to list format (flag/option for to-string methods)

.. code-block:: python
   :linenos:

   from search_query.parser import parse

   query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
   query = parse(query_string, platform="pubmed")
   wos_query = query.translate(target_syntax="wos")
   print(wos_query.to_string())
   # Output:
   # (AB="digital health" OR TI="digital health") AND (AB="privacy" OR TI="privacy")
