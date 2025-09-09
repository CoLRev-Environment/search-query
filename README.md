
<p align="center">
<img src="https://raw.githubusercontent.com/CoLRev-Environment/search-query/refs/heads/main/docs/source/_static/search_query_logo.svg" width="350">
</p>

<div align="center">

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/search-query/.github%2Fworkflows%2Ftests.yml?label=tests)](https://github.com/CoLRev-Environment/search-query/actions/workflows/tests.yml)
[![GitHub Release](https://img.shields.io/github/v/release/CoLRev-Environment/search-query)](https://github.com/CoLRev-Environment/search-query/releases/)
![Coverage](https://raw.githubusercontent.com/CoLRev-Environment/search-query/main/test/coverage.svg)
[![PyPI - Version](https://img.shields.io/pypi/v/search-query?color=blue)](https://pypi.org/project/search-query/)
[![GitHub License](https://img.shields.io/github/license/CoLRev-Environment/search-query)](https://github.com/CoLRev-Environment/search-query/releases/)
[![status](https://joss.theoj.org/papers/ea1fcafb8f80fa98bcbd857cf1cfada9/status.svg)](https://joss.theoj.org/papers/ea1fcafb8f80fa98bcbd857cf1cfada9)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb)

</div>

**Search Query** is a Python package designed to **load**, **lint**, **translate**, **save**, **improve**, and **automate** academic literature search queries.
It is extensible and currently supports PubMed, EBSCOHost, and Web of Science.
The package can be used programmatically, through the command line, or as a pre-commit hook.
It has zero dependencies and integrates in a variety of environments.
The parsers and linters are battle-tested on peer-reviewed [searchRxiv](https://www.cabidigitallibrary.org/journal/searchrxiv) queries.

## Installation

To install *search-query*, run:
```commandline
pip install search-query
```

## Quickstart

Creating a query programmatically is simple:
```python
from search_query import OrQuery, AndQuery

# Typical building-blocks approach
digital_synonyms = OrQuery(["digital", "virtual", "online"], field="abstract")
work_synonyms = OrQuery(["work", "labor", "service"], field="abstract")
query = AndQuery([digital_synonyms, work_synonyms])
```
A query can also be parsed from a string or a JSON search file (see the [overview of platform identifiers](https://colrev-environment.github.io/search-query/platforms/platform_index.html))
```python
from search_query.parser import parse

query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
query = parse(query_string, platform="pubmed")
```
The built-in **linter** functionality validates queries by identifying syntactical errors:
```python
from search_query.parser import parse

query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]'
query = parse(query_string, platform="pubmed")
# Output:
# ❌ Fatal: unbalanced-parentheses (PARSE_0002)
#   - Unbalanced opening parenthesis
#   Query: ("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]
#                                                ^^^
```
Once a `query` object is created, it can be translated for different databases.
The translation illustrates how the search for `Title/Abstract` is split into two elements:
```python
from search_query.parser import parse

query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract])'
pubmed_query = parse(query_string, platform="pubmed")
wos_query = pubmed_query.translate(target_syntax="wos")
print(wos_query.to_string())
# Output:
# (AB="digital health" OR TI="digital health") AND (AB="privacy" OR TI="privacy")
```
The translated query can be saved as follows:
```python
from search_query import SearchFile

search_file = SearchFile(
    filepath="search-file.json",
    search_string=wos_query.to_string(),
    platform="wos",
    version="1",
    authors=[{"name": "Tom Brady"}],
    record_info={},
    date={}
)

search_file.save()
```

For a more detailed overview of the package’s functionality, see the [documentation](https://colrev-environment.github.io/search-query/).

## Demo

A Jupyter Notebook demo (hosted on Binder) is available here:
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb)

## Encounter a problem?

Bug reports or issues can be submitted via [the issue tracker](https://github.com/CoLRev-Environment/search-query/issues) or by contacting the developers.

## How to cite

Eckhardt, P., Ernst, K., Fleischmann, T., Geßler, A., Schnickmann, K., Thurner, L., and Wagner, G. "search-query: An Open-Source Python Library for Academic Search Queries".

The package was developed as part of Bachelor's theses:

- Fleischmann, T. (2025). Advances in literature search queries: Validation and translation of search strings for EBSCOHost. Otto-Friedrich-University of Bamberg.
- Geßler, A. (2025). Design of an Emulator for API-based Academic Literature Searches. Otto-Friedrich-University of Bamberg.
- Schnickmann, K. (2025). Validating and Parsing Academic Search Queries: A Design Science Approach. Otto-Friedrich-University of Bamberg.
- Eckhardt, P. (2025). Advances in literature searches: Evaluation, analysis, and improvement of Web of Science queries. Otto-Friedrich-University of Bamberg.
- Ernst, K. (2024). Towards more efficient literature search: Design of an open source query translator. Otto-Friedrich-University of Bamberg.

## Alternative tools

This Python package is designed for programmatic and CLI-based use, as well as for integration into other literature management tools. For different scenarios, the following related tools may be helpful:

- [LitSonar](https://litsonar.com/)
- [Polyglot](https://sr-accelerator.com/#/polyglot)

## License

This project is distributed under the [MIT License](LICENSE).
