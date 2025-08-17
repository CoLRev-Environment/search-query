.. _improve:

Improve
==========================================================

The improve functionality of search-query depicts the query refinement step of a literature search.
This includes modification of the query.
The search space can be expanded to include plural forms and spelling variants by including wildcard operators and nested OR queries, as shown in the following examples.

Modification
---------------------

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

   if __name__ == "__main__":

      query = AndQuery([
         OrQuery(["labour", "employment"], field="title"),
         OrQuery(["robot", "algorith"], field="title")
      ], field="title")

      expand_spelling_variants(query)
      add_plural_wildcards(query)

      print(query.to_string(platform="pubmed"))

Evaluation
---------------------

See Cooper et al. 2018

.. code-block:: python
   :linenos:

   from search_query import AndQuery, OrQuery
   records_dict = {
      "r1": {
         "title": "Microsourcing platforms for online labor",
         "colrev_status": "rev_included"
      },
      "r2": {
         "title": "Online work and the future of microsourcing",
         "colrev_status": "rev_included"
      },
      "r3": {
         "title": "Microsourcing case studies",
         "colrev_status": "rev_excluded"
      },
      "r4": {
         "title": "Freelancing and online job platforms",
         "colrev_status": "rev_excluded"
      },
   }

   query = AndQuery([
      OrQuery(["microsourcing"], field="title"),
      OrQuery(["online"], field="title")
   ], field="title")

   # Evaluate the search
   results = query.evaluate(records_dict)
   print(f"Recall: {results['recall']}")
   print(f"Precision: {results['precision']}")
   print(f"F1 Score: {results['f1_score']}")
   # Output:
   # Recall: 1.0
   # Precision: 1.0
   # F1 Score: 1.0

..
   - functions to visualize (e.g., plot the distribution of results over time, etc.)
   - functions to compare (e.g., compare the results of two queries, etc.)

References
----------------

.. parsed-literal::

   Cooper C, Varley-Campbell J, Booth A, et al. (2018) Systematic review identifies six metrics and one method for assessin
      literature search effectiveness but no consensus on appropriate use. Journal of Clinical Epidemiology 99: 53–63.
      DOI: 10.1016/J.JCLINEPI.2018.02.025.
