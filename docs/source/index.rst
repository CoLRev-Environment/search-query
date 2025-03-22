Search-Query Documentation
========================================

.. image:: https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/search-query/.github%2Fworkflows%2Ftests.yml?label=tests
   :target: https://github.com/CoLRev-Environment/search-query/actions/workflows/tests.yml

.. image:: https://img.shields.io/github/v/release/CoLRev-Environment/search-query
   :target: https://github.com/CoLRev-Environment/search-query/releases/

.. image:: https://img.shields.io/pypi/v/search-query?color=blue
   :target: https://pypi.org/project/search-query/

.. image:: https://img.shields.io/github/license/CoLRev-Environment/search-query
   :target: https://github.com/CoLRev-Environment/search-query/releases/

.. image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb

Search-query is a Python package for **translating academic literature search queries (i.e., parsing and serializing)**, but also for **validating, simplifying, and improving** them.
It implements various syntax validation checks ("linters" for search queries) and prints instructive messages to inform users about potential issues.

We currently support PubMed, EBSCOHost, and Web of Science, but plan to extend search-query to support other databases.
As a default it relies on the JSON schema proposed by an expert panel (Haddaway et al., 2022).
The package can be used programmatically or through the command line, has zero dependencies, and can therefore be integrated in a variety of environments.
The heuristics, parsers, and linters are battle-tested on over 500 peer-reviewed queries registered at `searchRxiv <https://www.cabidigitallibrary.org/journal/searchrxiv>`_.

A demo in a Jupyter Notebook (hosted on Binder) is available here:

.. image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb

Installation
============

To install `search-query`, run:

.. code-block:: bash

    pip install search-query


Programmatic Use
================

To create a query programmatically, run:

.. code-block:: python

    from search_query import OrQuery, AndQuery

    # Typical building-blocks approach
    digital_synonyms = OrQuery(["digital", "virtual", "online"], search_field="Abstract")
    work_synonyms = OrQuery(["work", "labor", "service"], search_field="Abstract")
    query = AndQuery([digital_synonyms, work_synonyms], search_field="Author Keywords")

Parameters:

- list of strings or queries: strings that you want to include in the search query,
- ``search_field``: search field to which the query should be applied (available options: TODO — provide examples and link to docs)

..
   Search strings can be either in string or list format.

Search-query can parse queries from strings and JSON files in the standard format (Haddaway et al. 2022). Example:

.. code-block:: json

   {
      "record_info": {},
      "authors": [{"name": "Wagner, G.", "ORCID": "0000-0000-0000-1111"}],
      "date": {"data_entry": "2019.07.01", "search_conducted": "2019.07.01"},
      "platform": "Web of Science",
      "database": ["SCI-EXPANDED", "SSCI", "A&HCI"],
      "search_string": "TS=(quantum AND dot AND spin)",
   }

To load a JSON query file, run the parser:

.. code-block:: python

    from search_query.search_file import SearchFile
    from search_query.parser import parse

    search = SearchFile("search-file.json")
    query = parse(search.search_string, syntax=search.platform)

Available platform identifiers are listed :doc:`here </parser/parser_index>`.

Linters
----------------

Each query parser has a corresponding linter that checks for errors and warnings in the query.
To validate a JSON query file, run the linter:

.. code-block:: python

    from search_query.linter import run_linter

    messages = run_linter(search.search_string, syntax=search.platform)
    print(messages)

There are two modes:

- **Strict mode**: Forces the user to maintain clean, valid input but at the cost of convenience. This mode fails on fatal or error outcomes and prints warnings.
- **Non-strict mode**: Focuses on usability, automatically resolving common issues while maintaining transparency via warnings. This mode fails only on fatal outcomes. Auto-corrects errors as much as possible and prints a message (adds a fatal message if this is not possible). Prints warnings.

An additional "silent" option may be used to silence warnings.

Query translation
-----------------------------

To translate a query to a particular database syntax and print it, run:

.. code-block:: python

    query.to_string(syntax="ebsco")
    query.to_string(syntax="pubmed")
    query.to_string(syntax="wos")

To write a query to a JSON file, run the serializer:

.. code-block:: python

    from search_query import save_file

    save_file(
        filename="search-file.json",
        query_str=query.to_string(syntax="wos"),
        syntax="wos",
        authors=[{"name": "Tom Brady"}],
        record_info={},
        date={}
    )


CLI Use
=======

Linters can be run on the CLI:

.. code-block:: bash

    search-file-lint search-file.json


Pre-commit Hooks
================

Linters can be included as pre-commit hooks by adding the following to the ``.pre-commit-config.yaml``:

.. code-block:: yaml

    repos:
      - repo: https://github.com/CoLRev-Environment/search-query
        rev: main  # or version of search-query
        hooks:
          - id: search-file-lint

For development and testing, use the following:

.. code-block:: yaml

    repos:
      - repo: local
        hooks:
          - id: search-file-lint
            name: Search-file linter
            entry: search-file-lint
            language: python
            files: \.json$

To activate and run:

.. code-block:: bash

    pre-commit install
    pre-commit run --all


Parser development
-------------------------

To develop a parser, see `dev-parser <dev_docs/parser.html>`_ docs.


References
----------------

Haddaway, N. R., Rethlefsen, M. L., Davies, M., Glanville, J., McGowan, B., Nyhan, K., & Young, S. (2022). A suggested data structure for transparent and repeatable reporting of bibliographic searching. *Campbell Systematic Reviews*, 18(4), e1288. doi:`10.1002/cl2.1288 <https://onlinelibrary.wiley.com/doi/full/10.1002/cl2.1288>`_


.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Contents:

   parser/parser_index
   messages/errors_index
   dev_docs/parser
