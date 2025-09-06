## How to contribute

Thank you for your interest in contributing to the *search-query* package!
We encourage you to have a look at our [open issues](https://github.com/CoLRev-Environment/search-query/issues) or open a new one if you encounter an un-addressed problem.

Here are some guidelines for how to contribute to the package.

**Want to implement a new search platform?**

Right now, the package supports a limited amount of search platforms.
We therefore appreciate help in expanding the package with new platforms.
If you’re unsure which platform to implement, check our [platform roadmap](https://github.com/CoLRev-Environment/search-query/issues/46).

Our [development documentation](https://colrev-environment.github.io/search-query/dev_docs/overview.html) includes an overview of best practices for implementing a new search platform, along with code skeletons to help you get started.

**Found a bug?**

If you found a bug or encountered any issues while using the package, you can contribute by [opening an issue](https://github.com/CoLRev-Environment/search-query/issues/new).
When possible, include a minimal code example and describe the expected behavior.

**Running and extending the test suite**

We use [`pytest`](https://docs.pytest.org/) for testing.
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
* If you implement a new search platform, include tests for end-to-end search-query functionality

**Other ways to contribute**

Of course, we also welcome smaller contributions, such as bug fixes or improvements to the package documentation.
<!-- TODO: Include guide for contributing to docs? -->

If you’ve made changes to the source code or documentation, fork the repository and open a [pull request](https://github.com/CoLRev-Environment/search-query/compare).
Please include a clear description of your changes.

### Adding a new parser/serializer version

When evolving a platform syntax, add a new version directory and keep older
versions intact:

1. Copy the previous version directory (e.g., `pubmed/v1_0_0` → `pubmed/v1_1_0`).
2. Implement the required changes in parser, serializer, and translator files.
3. Register the new classes in `search_query/parser.py`,
   `search_query/serializer.py`, and `search_query/translator.py`.
4. Add tests and golden files covering the new version.


Thanks,

The *search-query* team
