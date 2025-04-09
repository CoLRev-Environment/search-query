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
It implements various syntax validation checks (aka. linters) and prints instructive messages to inform users about potential issues.
These checks are valuable for preventing errors—an important step given that previous studies have found high error rates in search queries (Li & Rainer, 2023: **50%**; Salvador-Oliván et al., 2019: **90%**; Sampson & McGowan, 2006: **80%**).

We currently support PubMed, EBSCOHost, and Web of Science, but plan to extend search-query to support other databases.
The package can be used programmatically or through the command line, has zero dependencies, and can therefore be integrated in a variety of environments.
The parsers, and linters are battle-tested on over **500 (TO UPDATE)** peer-reviewed queries registered at `searchRxiv <https://www.cabidigitallibrary.org/journal/searchrxiv>`_.

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

We can also parse a query from a string or a `JSON search file <#json-search-files>`_ (see the :doc:`overview of platform identifiers (syntax) </parser/parser_index>`):

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

Another useful feature of search-query is its **validation (linter)** functionality, which helps us to identify syntactical errors:

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


.. _json-search-files:

JSON search files
-----------------------

Search-query can parse queries from strings and JSON files in the standard format (Haddaway et al. 2022). Example:

.. code-block:: json

   {
      "record_info": {},
      "authors": [{"name": "Wagner, G.", "ORCID": "0000-0000-0000-1111"}],
      "date": {"data_entry": "2019.07.01", "search_conducted": "2019.07.01"},
      "platform": "Web of Science",
      "database": ["SCI-EXPANDED", "SSCI", "A&HCI"],
      "search_string": "TS=(quantum AND dot AND spin)"
   }

To load a JSON query file, run the parser:

.. code-block:: python

    from search_query.search_file import SearchFile
    from search_query.parser import parse

    search = SearchFile("search-file.json")
    query = parse(search.search_string, syntax=search.platform)

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

.. parsed-literal::

   Haddaway, N. R., Rethlefsen, M. L., Davies, M., Glanville, J., McGowan, B., Nyhan, K., & Young, S. (2022).
     A suggested data structure for transparent and repeatable reporting of bibliographic searching.
     *Campbell Systematic Reviews*, 18(4), e1288. doi: `10.1002/cl2.1288 <https://onlinelibrary.wiley.com/doi/full/10.1002/cl2.1288>`_

    Li, Z., & Rainer, A. (2023). Reproducible Searches in Systematic Reviews: An Evaluation and Guidelines.
      IEEE Access, 11, 84048–84060. IEEE Access. doi: `10.1109/ACCESS.2023.3299211 <https://doi.org/10.1109/ACCESS.2023.3299211>`_

    Salvador-Oliván, J. A., Marco-Cuenca, G., & Arquero-Avilés, R. (2019).
      Errors in search strategies used in systematic reviews and their effects on information retrieval.
      Journal of the Medical Library Association : JMLA, 107(2), 210. doi: `10.5195/jmla.2019.567 <https://doi.org/10.5195/jmla.2019.567>`_

    Sampson, M., & McGowan, J. (2006). Errors in search strategies were identified by type and frequency.
      Journal of Clinical Epidemiology, 59(10), 1057–1063. doi: `10.1016/j.jclinepi.2006.01.007 <https://doi.org/10.1016/j.jclinepi.2006.01.007>`_


.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Manual

   parser/parser_index
   messages/errors_index
   api_search/api_search

.. toctree::
   :hidden:
   :caption: Developer documentation
   :maxdepth: 1

   dev_docs/parser
