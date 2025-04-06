.. _api_search:

API searches
==========================================================

This example demonstrates how to construct a search query using the
``search-query`` package and use it with a custom function that queries the Crossref API.

.. code-block:: python
   :linenos:

    from colrev.packages.crossref.src import crossref_api
    
    from typing import Iterator
    from search_query.constants import Fields, Operators
    from search_query.or_query import OrQuery
    from search_query.query import Query

    def to_string_crossref(node: Query) -> str:
       """Translate query into a Crossref-compatible query string."""
       if node.value != Operators.OR:
           raise ValueError("Crossref serializer only supports OR queries.")

       query_parts = []

       for child in node.children:
           if child.operator:
               raise ValueError("Nested operators are not supported in Crossref serializer.")

           if child.search_field.value != Fields.TITLE:
               raise ValueError(f"Only title field is supported in Crossref serializer ({child.search_field})")

           query_parts.append(child.value.strip())

       # Crossref uses '+' for spaces in query values
       query_string = "+".join(query_parts)
       return f"https://api.crossref.org/works?query.title={query_string}"

    def run_crossref_api_search(query: Query) -> Iterator[dict]:
        url = to_string_crossref(query)
        api_crossref = crossref_api.CrossrefAPI(params={"url": url})
    
        api_crossref.check_availability()
        return api_crossref.get_records()
    
    if __name__ == "__main__":
        query = OrQuery(["digital", "online"], search_field="ti")
        records = run_crossref_api_search(query)

Furthermore, custom functions can be used to save the search parameters, such as the date on which the search was performed or the search query. An example of such a function is depicted below:

.. code-block:: python
   :linenos:

    def log_search_history(file_path: Path, query: Query):
      entry = {
          "date_executed": datetime.now(timezone.utc).isoformat(),
          "query": f"{query.to_string()}"
      }
  
      with open(file_path, 'a', encoding='utf-8') as file:
          file.write(json.dumps(entry, indent=4) + '\n\n')
  
    if __name__ == "__main__":
      file_path = "example/log_search_history.json"
      result = log_search_history(Path(file_path), query)

Also, the resulting records of the search results can be saved in a file. A simple Python function to save the results could look like this:

.. code-block:: python
   :linenos:

    def save_records(file_path: Path, results: list):
        with open(file_path, 'w', encoding='utf-8') as file:
            for record in results:
                file.write(str(record) + '\n\n')


