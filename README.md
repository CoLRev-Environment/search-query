
<p align="center">
<img src="docs/source/_static/search_query_logo.svg" width="350">
</p>

<div align="center">

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/search-query/.github%2Fworkflows%2Ftests.yml?label=tests)](https://github.com/CoLRev-Environment/search-query/actions/workflows/tests.yml)
[![GitHub Release](https://img.shields.io/github/v/release/CoLRev-Environment/search-query)](https://github.com/CoLRev-Environment/search-query/releases/)
![Coverage](https://raw.githubusercontent.com/CoLRev-Environment/search-query/main/test/coverage.svg)
[![PyPI - Version](https://img.shields.io/pypi/v/search-query?color=blue)](https://pypi.org/project/search-query/)
[![GitHub License](https://img.shields.io/github/license/CoLRev-Environment/search-query)](https://github.com/CoLRev-Environment/search-query/releases/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CoLRev-Environment/search-query/HEAD?labpath=docs%2Fsource%2Fdemo.ipynb)

</div>

**Search Query** is a Python package designed to **load**, **lint**, **translate**, **save**, **improve**, and **automate** academic literature search queries.
It is extensible and currently supports PubMed, EBSCOHost, and Web of Science.
The package can be used programmatically, through the command line, or as a pre-commit hook.
It has zero dependencies and integrates in a variety of environments.
The parsers and linters are battle-tested on peer-reviewed [searchRxiv](https://www.cabidigitallibrary.org/journal/searchrxiv) queries.

For more information, see the [documentation](https://colrev-environment.github.io/search-query/).

## How to cite

Eckhardt, P., Ernst, K., Fleischmann, T., Geßler, A., Schnickmann, K., Thurner, L., and Wagner, G. "search-query: An Open-Source Python Library for Academic Search Queries".

The package was developed as part of Bachelor's theses:

- Fleischmann, T. (2025). Advances in literature search queries: Validation and translation of search strings for EBSCO host. Otto-Friedrich-University of Bamberg.
- Geßler, A. (2025). Design of an Emulator for API-based Academic Literature Searches. Otto-Friedrich-University of Bamberg.
- Schnickmann, K. (2025). Validating and Parsing Academic Search Queries: A Design Science Approach. Otto-Friedrich-University of Bamberg.
- Eckhardt, P. (2025). Advances in literature searches: Evaluation, analysis, and improvement of Web of Science queries. Otto-Friedrich-University of Bamberg.
- Ernst, K. (2024). Towards more efficient literature search: Design of an open source query translator. Otto-Friedrich-University of Bamberg.

## Not what you are looking for?

This Python package was developed with purpose of integrating it into other literature management tools. If that isn't your use case, it might be useful for you to look at these related tools:

- [LitSonar](https://litsonar.com/)
- [Polyglot](https://sr-accelerator.com/#/polyglot)

## License

This project is distributed under the [MIT License](LICENSE).
