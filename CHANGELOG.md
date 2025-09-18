# Changelog
All notable changes to this project will be documented in this file.

## Unreleased

- No changes yet.

## Release 0.13.0

- **Versioned platform architecture & upgrades**: Introduced version-aware parser registry that selects list or string parsers per platform version and defaults to the latest registered release. Auto-discovery for parser, serializer, and translator implementations. Added an upgrade pipeline that routes through the generic query as an intermediate representation, exposed through a new `upgrade` CLI subcommand.
- **CLI improvements**: Rebuilt the CLI around explicit `translate`, `lint`, and `upgrade` sub-commands with improved error handling and user feedback, including success messages emitted by the linter workflow.
- **Search file handling**: Refactored `SearchFile` to replace `filepath` with `search_results_path`, derive the default history path, ensure directories exist when saving, and exclude private attributes from serialization output.
- **Linter updates**: Added the `deprecated-syntax` warning (`LINT_2001`) to guide users toward upgrading queries that rely on legacy syntax.
- **Documentation**: Documented the syntax upgrade workflow and versioning policy for database-specific queries, including CLI examples.

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
