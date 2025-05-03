.. _pre_commit:

Pre-commit hooks
==========================================================

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
