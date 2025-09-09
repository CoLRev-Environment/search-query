## How to contribute

Contributions to the *search-query* package are welcome.
The [open issues](https://github.com/CoLRev-Environment/search-query/issues) highlight outstanding problems and potential enhancements.

The following guidelines describe how to contribute to the package.

**Want to implement a new search platform?**

Right now, the package supports a limited number of search platforms.
Help in expanding the package with new platforms is appreciated.
The [platform roadmap](https://github.com/CoLRev-Environment/search-query/issues/46) indicates priority areas.

The [development documentation](https://colrev-environment.github.io/search-query/dev_docs/overview.html) provides an overview of best practices for implementing a new search platform, along with code skeletons.

**Found a bug?**

Bug reports and other issues can be submitted via [the issue tracker](https://github.com/CoLRev-Environment/search-query/issues/new).
A minimal code example and a description of expected behavior facilitate triage.

**Running and extending the test suite**

[`pytest`](https://docs.pytest.org/) is used for testing.
Tests are located in the `tests/` directory and are organized by functionality (e.g., linting, parsing, platform-specific implementations).

To run all tests locally:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run the complete test suite
pytest test
````

To run a specific test file or function:

```bash
pytest test/test_parser.py
pytest test/test_parser.py::test_get_platform
```

To see detailed output (helpful for debugging):

```bash
pytest -vv
```

Adding new tests

* Place new test files in the `test/` directory, following the `test_*.py` naming convention.
* Group related tests into logical classes or functions.
* Use clear and descriptive test names (`test_what_it_does`).
* Prefer [pytest parameterization](https://docs.pytest.org/en/stable/how-to/parametrize.html) when testing multiple input–output pairs.
* Implementing a new search platform should include tests for end-to-end search-query functionality.

**Other ways to contribute**

Smaller contributions, such as bug fixes or improvements to the package documentation, are also appreciated.
<!-- TODO: Include guide for contributing to docs? -->

After making changes to the source code or documentation, fork the repository and open a [pull request](https://github.com/CoLRev-Environment/search-query/compare) with a clear description of the changes.

### Adding a new parser/serializer version

When evolving a platform syntax, add a new version directory and keep older
versions intact:

1. Copy the previous version directory (e.g., `pubmed/v1` → `pubmed/v2`).
2. Implement the required changes in parser, serializer, and translator files.
3. Register the new classes in `search_query/parser.py`,
   `search_query/serializer.py`, and `search_query/translator.py`.
4. Add tests and golden files covering the new version.


Thanks,

The *search-query* team
