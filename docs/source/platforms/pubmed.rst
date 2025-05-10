.. _pubmed:

PubMed
====================

Run a query
--------------

Queries can be executed in the [basic search box](https://pubmed.ncbi.nlm.nih.gov/) or the advanced [Query box](https://pubmed.ncbi.nlm.nih.gov/advanced/).

Report a query
-----------------

It is recommended to store the queries entered in the basic or advanced box as the *search_string* and leave the *general_search_field* empty.

TODO : interface illustration?

The advanced search page also offers the option to "Add terms to the query box" (by selecting specific fields in the drop-down).
This box offers a convenient way to add queries and apply the same search field (from the drop-down menu) to the whole query.
Here, it is important to
- use search fields only in the *general_search_field*
- when running the same query with different serach fields, as in this `example <https://www.cabidigitallibrary.org/doi/10.1079/SEARCHRXIV.2023.00236>`_, *search-query* will assume that the queries are added with an "OR" operator.

TODO : interface illustration (highlight "OR"  button)

TODO : add a linter warning (convention) when multiple general_search_fields are given? (operator unclear)


Note: We assume that the [basic search box](https://pubmed.ncbi.nlm.nih.gov/) and the advanced [Query box](https://pubmed.ncbi.nlm.nih.gov/advanced/) handle queries equivalently.

Resources:

- `PubMed User Guide <https://pubmed.ncbi.nlm.nih.gov/help/>`_
