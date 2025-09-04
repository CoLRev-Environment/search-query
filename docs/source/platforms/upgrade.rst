.. _upgrade:

Upgrade Queries Between Syntax Versions
=======================================

The ``search-query`` package allows you to **upgrade database-specific queries**
from one syntax version to another.

Most users will interact with this feature via the **command-line interface (CLI)**.
Behind the scenes, the upgrade follows a structured procedure using a generic query, or
intermediate representation (IR).

Quick Start (CLI)
-----------------

To upgrade a query stored in ``query.json`` to version ``2.0.0``:

.. code-block:: console

   search-query upgrade query.json --to 2.0.0

If ``--to`` is omitted or set to ``latest``, the tool automatically selects
the latest supported version for the specified platform.

.. tip::

   The upgraded query will be written back to the file (or another location if
   specified with ``--output``).

How It Works Internally
-----------------------

Even though you only call the CLI, the following procedure happens under the hood:

1. **Parse**
   The query string (platform + current version) is parsed into a query object.

2. **Translate to Generic Syntax (IR)**
   The query is converted into a generic query object, i.e., a platform-agnostic intermediate representation.

3. **Translate to Target Syntax**
   The generic query is mapped into the target platform/version query model.

4. **Serialize**
   The new query object is serialized into a query string.

5. **Validate**
   The upgraded query is re-parsed in the target version to ensure syntactic validity.

This design ensures:

- **Maintainability**: only one parser/translator/serializer per platform+version.
- **Consistency**: every upgrade path goes through the same IR.
- **Transparency**: lossy conversions trigger warnings instead of silent failures.
- **Extensibility**: adding a new version or platform is linear work.

Example Workflow
----------------

Suppose you maintain a PubMed query in an older syntax (``1.0.0``) and want to upgrade it:

.. code-block:: console

   search-query upgrade pubmed_query.json --to latest

This will:

- Parse the PubMed v1.0.0 query,
- Convert it into the generic query representation,
- Translate it into the latest PubMed syntax,
- Serialize and validate the upgraded query.

Design Note
-----------

By pivoting through the **generic query IR**, the upgrade avoids the need for
``O(N^2)`` pairwise converters. Each platform/version only needs:

- **Parser** – to read queries,
- **Translator** – to/from the IR,
- **Serializer** – to output queries.
