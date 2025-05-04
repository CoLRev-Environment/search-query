
# Change Log
All notable changes to this project will be documented in this file.

## Release 0.11.0

- Refactoring (AND/OR/NOT-Queries, method signatures, public to private methods)
- Rename methods: `query.translate_xy()` to `query.write(platform=xy)`, `query.print_query_xy()` to `query.to_string(platform=xy)`
- Integrate Query tree into node attribute
- Make dev dependencies optional
- Add tests on GitHub actions
- Extract constants
- Code skeleton for Parsers and Linters
- Documentation: Sphinx
- SearchFields instead of str
- Binder demo
- Implement `Query.selects()`
- Drop ABC inheritance
- Add `is_term()` and `is_operator()`

## Release 0.10.0

First basic implementation of a search query translator.

Included databases for translation:
- PubMed
- Web of Science - Core Collection
- IEEE Xplore
