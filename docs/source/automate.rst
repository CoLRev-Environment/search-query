.. _automate:

Automate
==========================================================

Search-query can be used to automate different steps of the search process,
such as searching for records in an API, filtering retrieved records, storing
the results, and creating a search file.


API retrieval
----------------------------------------------------------

Search queries can be used as part of automated API-based literature searches.
The following example uses a search-query term to construct a Crossref request,
retrieve the corresponding records, store them as a BibTeX file, and document
the search in a search file.

.. dropdown:: Installation requirements
   :icon: info

   The example below requires the ``colrev`` package to be installed. You can
   install it via pip:

   .. code-block:: bash

      pip install colrev==0.16.1

   **Important**: ``colrev`` version 0.16.1 requires Python **3.10** or higher.
   If you are on a different Python version, create a Python 3.10 environment
   (e.g., via ``uv``, ``venv``, or ``conda``) before installing.

.. code-block:: python
   :linenos:

   import datetime
   from pathlib import Path
   from urllib.parse import quote_plus

   from colrev.packages.crossref.src import crossref_api
   from colrev.writer.write_utils import write_file

   from search_query.constants import Fields
   from search_query.query import Query
   from search_query.query_term import Term
   from search_query.search_file import SearchFile


   def to_crossref_url(query: Query) -> str:
       """Create a Crossref URL for an individual search term."""
       if not query.is_term():
           raise ValueError(
               "Crossref retrieval expects an individual search term."
           )

       if query.field is None or query.field.value != Fields.TITLE:
           raise ValueError(
               f"Only the title field is supported in this example "
               f"({query.field})."
           )

       query_value = query.value.strip().strip('"')

       return (
           "https://api.crossref.org/works"
           f"?query.title={quote_plus(query_value)}"
       )


   if __name__ == "__main__":

       query = Term(
           "microsourcing",
           field="title",
       )

       url = to_crossref_url(query)

       api_crossref = crossref_api.CrossrefAPI(url=url)
       records = api_crossref.get_records()

       sf = SearchFile(
           search_string=query.to_string(),
           platform="crossref",
           authors=[{"name": "Gerit Wagner"}],
           record_info={
               "source": "manual",
               "url": url,
           },
           date={
               "data_entry": datetime.datetime.now().strftime(
                   "%Y-%m-%d %H:%M"
               )
           },
           field="title",
           description="Crossref search for research on microsourcing",
       )

       sf.save("test/microsourcing_search.json")

       records_dict = {
           record.get_value("doi"): record.get_data()
           for record in records
       }

       write_file(
           records_dict=records_dict,
           filename=Path("test/crossref_records.bib"),
       )


Query emulation
----------------------------------------------------------

Some academic search APIs only support simple keyword searches and cannot
execute nested Boolean queries directly. In such cases, the query tree provided
by search-query can be used to implement an independent query-processing layer.

The following example illustrates the retrieval approach of **QuEALS (Query
Emulation for Academic Literature Searches)** using the Crossref API. QuEALS
recursively processes a search-query tree and combines API-based retrieval with
local query processing.

The approach is described in:

**Geßler, A., Schnickmann, K.**, and Wagner, G. (2026). “Advancing literature
review automation through API-based searches: Design of an independent
emulator”. Conditionally accepted: *Proceedings of the International Conference
on Information Systems*.

.. note::

   Crossref-specific retrieval functionality is intentionally not part of the
   search-query package. The example demonstrates how search-query can provide
   the query representation and local processing required for query emulation,
   while API-specific retrieval remains with the corresponding source
   implementation.

.. code-block:: python
   :linenos:

   from urllib.parse import quote_plus

   from colrev.packages.crossref.src import crossref_api

   from search_query.constants import Fields, Operators
   from search_query.query import Query
   from search_query.query_and import AndQuery
   from search_query.query_or import OrQuery


   def to_crossref_url(query: Query) -> str:
       """Create a Crossref URL for an individual search term."""
       if not query.is_term():
           raise ValueError(
               "Crossref retrieval expects an individual search term."
           )

       if query.field is None or query.field.value != Fields.TITLE:
           raise ValueError(
               f"Only the title field is supported in this example "
               f"({query.field})."
           )

       query_value = query.value.strip().strip('"')

       return (
           "https://api.crossref.org/works"
           f"?query.title={quote_plus(query_value)}"
       )


   def get_crossref_yield(query: Query) -> int:
       """Get the estimated number of records for an individual term."""
       url = to_crossref_url(query)

       api_crossref = crossref_api.CrossrefAPI(url=url)

       return api_crossref.get_len_total()


   def estimate_yield(query: Query) -> int:
       """Estimate the yield of a query recursively."""
       if query.is_term():
           return get_crossref_yield(query)

       estimates = [
           estimate_yield(child)
           for child in query.children
       ]

       if query.value == Operators.AND:
           return min(estimates)

       if query.value == Operators.OR:
           return sum(estimates)

       raise ValueError(f"Unsupported operator: {query.value}")


   def retrieve_term(query: Query) -> list[dict]:
       """Retrieve records for an individual search term from Crossref."""
       url = to_crossref_url(query)

       api_crossref = crossref_api.CrossrefAPI(url=url)
       records = api_crossref.get_records()

       return [
           record.get_data()
           for record in records
       ]


   def deduplicate(records: list[dict]) -> list[dict]:
       """Remove records retrieved through multiple query branches."""
       records_by_doi = {
           record["doi"]: record
           for record in records
       }

       return list(records_by_doi.values())


   def retrieve(query: Query) -> list[dict]:
       """Retrieve records using the QuEALS approach."""
       if query.is_term():
           return retrieve_term(query)

       if query.value == Operators.OR:
           records = []

           for child in query.children:
               records.extend(retrieve(child))

           return deduplicate(records)

       if query.value == Operators.AND:
           child = min(
               query.children,
               key=estimate_yield,
           )

           records = retrieve(child)

           return [
               record
               for record in records
               if query.selects(record_dict=record)
           ]

       raise ValueError(f"Unsupported operator: {query.value}")


   if __name__ == "__main__":

       query = AndQuery(
           [
               OrQuery(
                   ["strategy", "strategic"],
                   field="title",
               ),
               OrQuery(
                   ["technology", "digital"],
                   field="title",
               ),
           ]
       )

       records = retrieve(query)

       # See "Automated API retrieval" above for an example of creating
       # a SearchFile and writing the retrieved records to a BibTeX file.
