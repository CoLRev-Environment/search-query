.. raw:: html

    <h1 style="display:none;">Search-Query Documentation</h1>

.. raw:: html

   <div style="text-align: center;">
       <img src="_static/search_query_logo.svg" alt="Search Query Logo" width="350"><br><br>

       <img src="https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/search-query/.github%2Fworkflows%2Ftests.yml?label=tests" alt="Build Status"
            onclick="window.open('https://github.com/CoLRev-Environment/search-query/actions/workflows/tests.yml')">
       <img src="https://img.shields.io/github/v/release/CoLRev-Environment/search-query" alt="GitHub Release"
            onclick="window.open('https://github.com/CoLRev-Environment/search-query/releases/')">
       <img src="https://img.shields.io/pypi/v/search-query?color=blue" alt="PyPI Version"
            onclick="window.open('https://pypi.org/project/search-query/')">
       <img src="https://img.shields.io/github/license/CoLRev-Environment/search-query" alt="License"
            onclick="window.open('https://github.com/CoLRev-Environment/search-query/releases/')">
   </div><br>

**Search Query** is a Python package designed to **load**, **lint**, **translate**, **save**, **improve**, and **automate** academic literature search queries.
It is extensible and currently supports PubMed, EBSCOHost, and Web of Science.
The package can be used programmatically, through the command line, or as a pre-commit hook.
It has zero dependencies and integrates in a variety of environments.
The parsers and linters are battle-tested on peer-reviewed `searchRxiv <https://www.cabidigitallibrary.org/journal/searchrxiv>`_ queries.

Installation
============

To install `search-query`, run:

.. code-block:: bash

    pip install search-query


Quickstart
================

Creating a query programmatically is simple:

.. code-block:: python

    from search_query import OrQuery, AndQuery

    # Typical building-blocks approach
    digital_synonyms = OrQuery(["digital", "virtual", "online"], field="abstract")
    work_synonyms = OrQuery(["work", "labor", "service"], field="abstract")
    query = AndQuery([digital_synonyms, work_synonyms])

A query can also be parsed from a string or a `JSON search file <#json-search-files>`_ (see the :doc:`overview of platform identifiers </platforms/platform_index>`):

.. code-block:: python

    from search_query.parser import parse

    query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
    query = parse(query_string, platform="pubmed")


The built-in **linter** functionality validates queries by identifying syntactical errors:

.. code-block:: python

    from search_query.parser import parse

    query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]'
    query = parse(query_string, platform="pubmed")
    # Output:
    # ❌ Fatal: unbalanced-parentheses (PARSE_0002)
    #   - Unbalanced opening parenthesis
    #   Query: ("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]
    #                                                ^^^

Once a :literal:`query` object is created, it can be translated for different databases.
The translation illustrates how the search for :literal:`Title/Abstract` is split into two elements:

.. code-block:: python
   :linenos:

   from search_query.parser import parse

   query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
   pubmed_query = parse(query_string, platform="pubmed")
   wos_query = pubmed_query.translate(target_syntax="wos")
   print(wos_query.to_string())
   # Output:
   # (AB="digital health" OR TI="digital health") AND (AB="privacy" OR TI="privacy")

The translated query can be saved as follows:

.. code-block:: python
   :linenos:

   from search_query import SearchFile

   search_file = SearchFile(
      search_string=wos_query.to_string(),
      platform="wos",
      version="1",
      authors=[{"name": "Tom Brady"}],
      record_info={},
      date={}
   )

   search_file.save("search-file.json")

Demo
============

A Jupyter Notebook demo (hosted on Binder) is available here:

.. image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb

Functional overview
======================

The search-query package supports the entire lifecycle of academic search query management.
Below is a high-level overview of the core functionalities:

.. image:: presentation.png

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Contents:

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Manual

   load
   lint/index
   translate
   save
   improve
   automate

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Platforms

   platforms/platform_index
   platforms/syntax_upgrade

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Query database

   query_database/index
   query_database/submit

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Interfaces

   cli
   pre_commit

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Developer documentation

   dev_docs/overview
   dev_docs/parser_development
   dev_docs/linter_development
   dev_docs/translator_development
   dev_docs/serializer_development
   dev_docs/tests
   dev_docs/api
