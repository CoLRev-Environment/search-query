.. _improve:

Improve
==========================================================

TODO

.. code-block:: python
   :linenos:

   from search_query import AndQuery, OrQuery

   def add_plural_wildcards(query):
      """Recursively add wildcards for plural forms in term values."""
      if query.operator:
         for child in query.children:
               add_plural_wildcards(child)
      else:
         val = query.value
         if not val.endswith("*") and not val.endswith("s"):
               query.value = val + "*"


   BE_AE_MAP = {
      "labour": "labor",
      "organisation": "organization",
      "analyse": "analyze",
      "optimisation": "optimization",
      "behaviour": "behavior",
   }

   def expand_spelling_variants(query):
      """Recursively expand BE/AE spelling variations in term values."""
      if query.operator:
         for child in query.children:
               expand_spelling_variants(child)
      else:
         val_lower = query.value.lower()
         if val_lower in BE_AE_MAP:
               be = val_lower
               ae = BE_AE_MAP[be]
               query.value = f'({be} OR {ae})'


   query = AndQuery([
      OrQuery(["labour", "employment"], search_field="ti"),
      OrQuery(["robot", "algorith"], search_field="ti")
   ], search_field="ti")

   expand_spelling_variants(query)
   add_plural_wildcards(query)

   print(query.to_string(syntax="pubmed"))
