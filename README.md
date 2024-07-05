#  Welcome to search-query

<div align="center">

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/search-query/.github%2Fworkflows%2Ftests.yml?label=tests)](https://github.com/CoLRev-Environment/search-query/actions/workflows/tests.yml)
[![GitHub Release](https://img.shields.io/github/v/release/CoLRev-Environment/search-query)](https://github.com/CoLRev-Environment/search-query/releases/)
[![PyPI - Version](https://img.shields.io/pypi/v/search-query?color=blue)](https://pypi.org/project/search-query/)
[![GitHub License](https://img.shields.io/github/license/CoLRev-Environment/search-query)](https://github.com/CoLRev-Environment/search-query/releases/)
</div>

Search-query is a Python package to translate literature search queries across databases, such as PubMed and Web of Science.
It can be used programmatically, has zero dependencies, and can therefore be integrated in a variety of environments.
This package was developed as part of my Bachelor's thesis: Towards more efficient literature search: Design of an open source query translator.

## How to use?

To create queries, run:

```Python
from search_query import OrQuery, AndQuery

# Typical building-blocks approach
digital_synonyms = OrQuery(["digital", "virtual", "online"], search_field="Abstract")
work_synonyms = OrQuery(["work", "labor", "service"], search_field="Abstract")
query = AndQuery([digital_synonyms, work_synonyms], search_field="Author Keywords")

# Example combining queries and terms at the same level
query = AndQuery([digital_synonyms, work_synonyms, "policy"], search_field="Author Keywords")
```

Parameters:

- search terms: strings which you want to include in the search query,
- nested queries: queries whose roots are appended to the query,
- search field: search field to which the query should be applied (available options: `Author Keywords`, `Abstract`, `Author`, `DOI`, `ISBN`, `Publisher` or `Title`)

To write the translated queries to a JSON file or print them, run:

```Python
query.write("translationIEEE.json", syntax="ieee")
query.write("translationPubMed.json", syntax="pubmed")
query.write("translationWebofScience.json", syntax="wos")

    or

query.to_string(syntax="ieee")
query.to_string(syntax="pubmed")
query.to_string(syntax="wos")

```

The `write()` methods create a JSON file using the parameter file name
The `to_string()` methods returns the translated string

## How to install

```
pip install search-query
```

To develop search-query, run

```
pip install -e .
```

## How to cite

Ernst, K. (2024). Towards more efficient literature search: Design of an open source query translator. Otto-Friedrich-University of Bamberg.

## Not what you're looking for?

This python package was developed with purpose of integrating it into other literature management tools. If that isn't your use case, it migth be useful for you to look at these related tools:

- LitSonar: https://litsonar.com/
- Polyglot: https://sr-accelerator.com/#/polyglot

## License

This project is distributed under the [MIT License](LICENSE).
