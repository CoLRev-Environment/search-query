#  Welcome to search-query

<div align="center">

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/search-query/.github%2Fworkflows%2Ftests.yml?label=tests)](https://github.com/CoLRev-Environment/search-query/actions/workflows/tests.yml)
[![GitHub Release](https://img.shields.io/github/v/release/CoLRev-Environment/search-query)](https://github.com/CoLRev-Environment/search-query/releases/)
[![PyPI - Version](https://img.shields.io/pypi/v/search-query?color=blue)](https://pypi.org/project/search-query/)
[![GitHub License](https://img.shields.io/github/license/CoLRev-Environment/search-query)](https://github.com/CoLRev-Environment/search-query/releases/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb)

</div>

Search-query is a Python package for parsing, validating, simplifying, and serializing literature search queries.
It currently supports PubMed and Web of Science, and can be extended to support other databases.
As a default it relies on the JSON schema proposed by an expert panel (Haddaway et al., 2022).
The package can be used programmatically or through the command line, has zero dependencies, and can therefore be integrated in a variety of environments.
The heuristics, parsers, and linters are battle-tested on over 500 peer-reviewed queries registered at [searchRxiv](https://www.cabidigitallibrary.org/journal/searchrxiv).

## Installation

To install search-query, run:

```
pip install search-query
```

## Programmatic use

To create a query programmatically, run:

```Python
from search_query import OrQuery, AndQuery

# Typical building-blocks approach
digital_synonyms = OrQuery(["digital", "virtual", "online"], search_field="Abstract")
work_synonyms = OrQuery(["work", "labor", "service"], search_field="Abstract")
query = AndQuery([digital_synonyms, work_synonyms], search_field="Author Keywords")
```

Parameters:

- list of strings or queries: strings which you want to include in the search query,
- search field: search field to which the query should be applied (available options: TODO: GIVE EXAMPLES AND LINK TO DOCS)

**TODO : implement a user-friendly version of OrQuery / AndQuery, which accepts lists of strings/queries and search_fields as strings**

To load a JSON query file, run the parser:

```python
from search_query.search_file import SearchFile
from search_query.parser import parse

search = SearchFile("search-file.json")
query = parse(search.search_string, syntax=search.platform)
```

Available platform identifiers are listed [here](search_query/constants.py).

To validate a JSON query file, run the linter:

```Python
from search_query.linter import run_linter

messages = run_linter(search.search_string, syntax=search.platform)
print(messages)
```

Linter messages are documented and explained [here](docs/dev_linter.md).

To simplify and format a query, run:

```Python
query.format(*tbd: how to select/exclude rules?*)
```
To translate a query to a particular database syntax and print it, run:

```Python
query.to_string(syntax="ebsco")
query.to_string(syntax="pubmed")
query.to_string(syntax="wos")
```

To write a query to a JSON file, run the serializer:

```Python
from search_query import save_file

save_file(
    filename="search-file.json",
    query_str=query.to_string(syntax="wos"),
    syntax="wos",
    authors=[{"name": "Tom Brady"}],
    record_info={},
    date={}
)
```

## CLI use

Linters can be run on the CLI:

```
search-query lint search-file.json
```

## Pre-commit hooks

Linters can be included as pre-commit hooks by adding the following to the `.pre-commit-config.yaml:

```
repos:
  - repo: local
    hooks:
      - id: search-file-lint
        name: Search-file linter
        entry: search-file-lint
        language: python
        files: \.json$
```

<!--
TODO: the previous one should be for dev. Enable (based on [.pre-commit-hooks.yaml](https://github.com/pre-commit/pre-commit-hooks/blob/main/.pre-commit-hooks.yaml)):

```
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0  # Use the ref you want to point at
    hooks:
    -   id: trailing-whitespace
```
-->

To activate and run:

```
pre-commit install
pre-commit run --all
```

## Documentation

[docs](docs/readme.md)

## Demo

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb)

## How to cite

TODO: main citation

The package was developed as part of Bachelor's theses:

- Ernst, K. (2024). Towards more efficient literature search: Design of an open source query translator. Otto-Friedrich-University of Bamberg.

## Not what you are looking for?

This python package was developed with purpose of integrating it into other literature management tools. If that isn't your use case, it migth be useful for you to look at these related tools:

- [LitSonar](https://litsonar.com/)
- [Polyglot](https://sr-accelerator.com/#/polyglot)

## License

This project is distributed under the [MIT License](LICENSE).
