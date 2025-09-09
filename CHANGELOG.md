
# Changelog
All notable changes to this project will be documented in this file.

## Unreleased

- Introduced versioned parser, serializer, and translator dispatchers.
- Added upgrade pipeline and CLI command.
- Added `deprecated-syntax` linter warning (`LINT_2001`).
- Added Web of Science parser version `0` with support for field tags later
  marked as deprecated.

## Release 0.12.0

- **Platform Support:**
  - **PubMed:** [#26](https://github.com/CoLRev-Environment/search-query/pull/26)
  - **Web of Science:** [#20](https://github.com/CoLRev-Environment/search-query/pull/20)
  - **EBSCOHost:** [#19](https://github.com/CoLRev-Environment/search-query/pull/19)
    → Implemented full platform support including:
    - Parsers (supporting query-string and list formats)
    - Linters
    - Serializers
    - Translators
    → Enhanced parsing capabilities with artificial parentheses to correctly reflect operator precedence.
    → Linters now provide categorized messages across six dimensions: `parsing`, `structure`, `terms`, `fields`, `databases`, and `quality`.

- **Refactoring and Internals:**
  - Refactored core query classes and methods (`query_and`, `query_or`, `query_near`, etc.).
  - Improved tokenization logic and consolidated linter messages into structured groups.
  - Removed deprecated `linter-mode` and unreachable code paths.
  - Migrated to `uv` for dependency management and streamlined environment setup.

- **New Features and Improvements:**
  - Introduced a **query database** for programmatic retrieval and sharing of query examples.
  - Achieved **comprehensive unit test coverage**, exceeding 95% of the codebase.
  - Expanded and improved **documentation**, including developer guidelines and platform-specific usage notes.

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
