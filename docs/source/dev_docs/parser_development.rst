Parser
============

To parse a list format, the numbered sub-queries should be replaced to create a search string, which can be parsed with the standard string-parser. This helps to avoid redundant implementation.

.. literalinclude:: parser_skeleton.py
   :language: python


TODO :
- refer to SearchFieldGeneral here!?
- recommend to use a broad regex for search-fields (make sure it is mapped to the right token type) and use a validator to check whether the specific value (searchf-field) is valid.
