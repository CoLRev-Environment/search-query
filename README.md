<div align="center">

#  search-query

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

## Documentation

[docs](docs/readme.md)

## Demo

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb)

## How to cite

TODO: main citation

The package was developed as part of Bachelor's theses:

- Ernst, K. (2024). Towards more efficient literature search: Design of an open source query translator. Otto-Friedrich-University of Bamberg.

## Not what you are looking for?

This Python package was developed with purpose of integrating it into other literature management tools. If that isn't your use case, it might be useful for you to look at these related tools:

- [LitSonar](https://litsonar.com/)
- [Polyglot](https://sr-accelerator.com/#/polyglot)

## License

This project is distributed under the [MIT License](LICENSE).
