.. _pre_commit:

Pre-commit hooks
==========================================================

The ``search-query lint`` hook is a linter that automatically checks
search query files (JSON) for errors and formatting issues.
It is based on the ``search-query`` package and ensures that only valid,
well-structured queries are committed to the repository. This helps catch
mistakes early and keeps the project consistent without extra manual work.

Linters can be included as pre-commit hooks by adding the following to the ``.pre-commit-config.yaml``:

.. code-block:: yaml

    repos:
      - repo: https://github.com/CoLRev-Environment/search-query
        rev: main  # or version of search-query
        hooks:
          - id: search-query-lint

For development and testing, use the following:

.. code-block:: yaml

    repos:
      - repo: local
        hooks:
          - id: search-query-lint
            name: Search-file linter
            entry: search-query-lint
            language: python
            files: \.json$

To activate and run:

.. code-block:: bash

    pre-commit install
    pre-commit run --all


Examples
----------------------------------------------------------

**1. Catching unbalanced-parentheses (PARSE_0002 — unbalanced-parentheses)**

Suppose a JSON search query file has a syntax error (e.g., a
missing closing parenthesis). The linter catches it before commit:

.. code-block:: json

    {
      "query": "(\"digital health\"[Title/Abstract]) AND (\"privacy\"[Title/Abstract]"
    }

When a commit is attempted, ``search-query lint`` outputs an error:

.. code-block:: text

    ❌ Fatal: unbalanced-parentheses (PARSE_0002)
       - Unbalanced opening parenthesis
       Query: ("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]
                                                    ^^^

**Fix**: Check the parentheses in the query


**2. Unsupported field (FIELD_0001 — field-unsupported)**

Some databases do not support certain fields. For example, using an
unsupported field like ``IY`` will trigger a linter error.

.. code-block:: json

    {
      "query": "TI=term1 AND IY=2020"
    }

Output during commit:

.. code-block:: text

    ❌ Error: field-unsupported (FIELD_0001)
       - Search field is not supported for this database
       Query: TI=term1 AND IY=2020
                      ^^^

**Fix:** Replace or remove the unsupported field to match the target database’s
field syntax.


**3. Implicit operator precedence (STRUCT_0001 — implicit-precedence)**

Mixing ``AND`` and ``OR`` at the same level can be ambiguous. Add explicit
parentheses to make the precedence of operators explicit.

.. code-block:: text

    # PLATFORM.PUBMED
    "health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")

Output during commit:

.. code-block:: text

    ❌ Error: implicit-precedence (STRUCT_0001)
       - Operator changed at the same level (explicit parentheses are recommended)
       Query: "health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")
                          ^^^^^           ^^^
       Tip: Add parentheses to clarify how AND/OR should be grouped.

**Fix:** Make the intended grouping explicit.

.. code-block:: text

    # PLATFORM.PUBMED
    ("health tracking" OR ("remote" AND "monitoring")) AND ("mobile application" OR "wearable device")
