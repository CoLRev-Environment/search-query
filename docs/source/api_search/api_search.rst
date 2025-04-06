.. _api_search:

API searches
==========================================================

To run API searches, it is often necessary to represent a query in the form of a URL as opposed to a query string.
Using the Crossref API as an example, the following illustrates how to construct such a URL to retrieve and store records.

.. code-block:: python
   :linenos:

    from colrev.packages.crossref.src import crossref_api
    from colrev.writer.write_utils import write_file

    from search_query.constants import Fields, Operators
    from search_query.or_query import OrQuery
    from search_query import save_file

    def to_crossref_url(query):
       """Translate query into a Crossref-compatible URL."""
       if query.value != Operators.OR:
           raise ValueError("Crossref serializer only supports OR queries.")

       query_parts = []
       for child in query.children:
           if child.operator:
               raise ValueError("Nested operators are not supported in Crossref serializer.")
           if child.search_field.value != Fields.TITLE:
               raise ValueError(f"Only title field is supported in Crossref serializer ({child.search_field})")
           query_parts.append(child.value.strip())

       # Crossref uses '+' for spaces in query values
       query_string = "+".join(query_parts)
       return f"https://api.crossref.org/works?query.title={query_string}"

    if __name__ == "__main__":

        query = OrQuery(["digital", "online"], search_field="ti")

        url = to_crossref_url(query)
        api_crossref = crossref_api.CrossrefAPI(params={"url": url})
        records = api_crossref.get_records()

        save_file(
            filename="crossref_search_file.json",
            query_str=url,
            syntax="crossref",
            authors=[{"name": "Tom Brady"}],
            record_info={},
            date={}
        )

        write_file(records_dict=records, filename="crossref_records.bib")
