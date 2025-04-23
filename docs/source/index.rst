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

**Search-query** is a Python package designed to **load**, **lint**, **translate**, **save**, **improve**, and **automate** academic literature search queries.
It currently supports PubMed, EBSCOHost, and Web of Science, and it is extensible to support other databases.
The package can be used programmatically, through the command line, or as a pre-commit hook.
It has zero dependencies, and can therefore be integrated in a variety of environments.
The parsers, and linters are battle-tested on peer-reviewed queries registered at `searchRxiv <https://www.cabidigitallibrary.org/journal/searchrxiv>`_.

A Jupyter Notebook demo (hosted on Binder) is available here:

.. image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb

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
    digital_synonyms = OrQuery(["digital", "virtual", "online"], search_field="Abstract")
    work_synonyms = OrQuery(["work", "labor", "service"], search_field="Abstract")
    query = AndQuery([digital_synonyms, work_synonyms], search_field="Author Keywords")

..
    Parameters:

    - list of strings or queries: strings that you want to include in the search query,
    - ``search_field``: search field to which the query should be applied (available options: TODO — provide examples and link to docs)
   Search strings can be either in string or list format.

We can also parse a query from a string or a `JSON search file <#json-search-files>`_ (see the :doc:`overview of platform identifiers (syntax) </platforms/platform_index>`):

.. code-block:: python

    from search_query.parser import parse

    query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
    query = parse(query_string, syntax="pubmed")

Once we have created a :literal:`query` object, we can translate it for different databases.
Note how the syntax is translated and how the search for :literal:`Title/Abstract` is spit into two elements:

.. code-block:: python

    query.to_string(syntax="ebsco")
   # Output:
   # (TI("digital health") OR AB("digital health")) AND (TI("privacy") OR AB("privacy"))

    query.to_string(syntax="wos")
   # Output:
   # (TI=("digital health") OR AB=("digital health")) AND (TI=("privacy") OR AB=("privacy"))

Another useful feature of search-query is its **linter** functionality, which helps us to validate the query by identifying syntactical errors:

.. code-block:: python

    from search_query.parser import parse

    query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]'
    query = parse(query_string, syntax="pubmed")
    # Output:
    # Fatal: unbalanced-parentheses (F0002) at position 66:
    #   ("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]
    #                                                                    ^^

Beyond the instructive error message, additional information on the specific messages is available `here <messages/errors_index.html>`_.

..
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


Parser development
-------------------------

To develop a parser, see `dev-parser <dev_docs/parser.html>`_ docs.


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

   dev_docs/parser
