.. _automate:

Automate
==========================================================

Search-query can be used to automate different steps of the search process, such as searching for records in an API, storing the results, and creating a search file.

To run API searches, it is often necessary to represent a query in the form of a URL as opposed to a query string.
Using the Crossref API as an example, the following illustrates how to construct such a URL to retrieve and store records.

.. tip::

    The example below requires the ``colrev`` package to be installed. You can install it via pip:

   .. code-block:: bash

        pip install colrev==0.16.1


   **Important**: ``colrev`` version 0.16.1 requires Python **3.10** or higher. If you’re on a different Python version, create a Python 3.10 environment (e.g., via `uv`, `venv`, or `conda`) before installing.

.. code-block:: python
   :linenos:

   import datetime
   from pathlib import Path
   from colrev.packages.crossref.src import crossref_api
   from colrev.writer.write_utils import write_file

   from search_query.constants import Fields, Operators
   from search_query.query_or import OrQuery
   from search_query.search_file import SearchFile

   def to_crossref_url(query):
       """Translate query into a Crossref-compatible URL."""
       if query.value != Operators.OR:
           raise ValueError("Crossref serializer only supports OR queries.")

       query_parts = []
       for child in query.children:
           if child.operator:
               raise ValueError("Nested operators are not supported in Crossref serializer.")
           if child.field.value != Fields.TITLE:
               raise ValueError(f"Only title field is supported in Crossref serializer ({child.field})")
           query_parts.append(child.value.strip())

       # Crossref uses '+' for spaces in query values
       query_string = "+".join(query_parts)
       return f"https://api.crossref.org/works?query.title={query_string}"

   if __name__ == "__main__":

       query = OrQuery(["microsourcing", "lululemon"], field="title")

       url = to_crossref_url(query)
       api_crossref = crossref_api.CrossrefAPI(url=url)
       records = api_crossref.get_records()

       sf = SearchFile(
           search_string=query.to_string(),
           platform="crossref",
           authors=[{"name": "Gerit Wagner"}],
           record_info={"source": "manual", "url": url},
           date={"data_entry": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")},
           field="title",
           description="Search for research on microsourcing"
       )

       sf.save("test/microsourcing_search.json")

       records_dict = {record.get_value("doi"): record.get_data() for record in records}
       write_file(records_dict=records_dict, filename=Path("test/crossref_records.bib"))
