.. _upgrade:

Syntax Upgrades
===============

The ``search-query`` package allows you to **upgrade database-specific queries**
from one *database syntax version* to another.

Most users will interact with this feature via the **command-line interface (CLI)**.
Behind the scenes, the upgrade follows a structured procedure using a generic query
as an intermediate representation (IR).

Quick Start (CLI)
-----------------

To upgrade a query stored in ``query.json`` to the latest version of a given database syntax:

.. code-block:: console

   search-query upgrade query.json

By default, if you omit the ``--to`` option or set it to ``latest``,
the tool upgrades the query to the latest supported syntax version for the specified database.
You can also specify a particular target version explicitly using ``--to <version>``,
but in most cases, upgrading to the latest version (by omitting ``--to``) is recommended.
The upgraded query will be written back to the file (or another location if specified with ``--output``).

Versioning Policy
-----------------

.. note::

   **What does "syntax version" mean?**

   A *syntax version* identifies the **evolving query language of a database platform**
   (e.g., PubMed, Web of Science), not the version of this package.
   The latest package version (of ``search-query``) evolves independently and
   contains the most up-to-date parser/translator/serializer for the syntax versions it supports
   across databases.
   New package releases can improve or extend support for *existing* syntax versions
   without implying that the database syntax itself changed.

Version identifiers follow a pragmatic schema aligned with semantic versioning,
with emphasis on **MAJOR** and **MINOR** to reflect database syntax evolution:

* **MAJOR** – *Breaking* syntax changes in the **database**
  (e.g., operators changed/removed, search fields renamed/removed, precedence rules altered).
  Older queries may need migration.

* **MINOR** – *Backward-compatible* syntax extensions
  (e.g., new search fields, additional operators, increased limits on terms or clauses).
  Older queries still parse and run.

..
   * **PATCH** – Non-semantic tweaks in this package’s handling of a DSV
   (bug fixes, robustness, diagnostics). Patch bumps do **not** imply a database syntax change.

.. important::

   The **primary use cases** are to

   1. store queries in the **current syntax version**,
   2. **upgrade** them to a newer syntax version when available, and
   3. **anticipate** that the database syntax may evolve (occasionally via new MAJOR versions).

   Full support for arbitrarily many **historic** syntax versions
   (including fine-grained distinctions and *backward* translation) is **not** a primary goal.
   Syntax versions start with 1.0 as of 2025-09-01. Previous versions will not be
   explored systematically and version 0.0 may be used as a placeholder for all previous syntax versions.

Observability of Syntax Versions
--------------------------------

Observability of *historic* versions is often limited because providers rarely
publish precise, comprehensive changelogs of syntax rules.
What matters most is that the **current/latest syntax is observable** (i.e., can be tested)
and that **material evolutions** in a database’s syntax can be recognized.
As a result:

- Old syntax versions may be only partially reconstructable.
- The focus is ensuring the **latest/current syntax** is well covered and testable.
- When a significant change is detected, the package encodes it as a new syntax version and
  provides **upgrade** paths via the IR.

How It Works Internally
-----------------------

Even though you only call the CLI, the following procedure happens under the hood:

1. **Parse**
   The query string (including platform and its current syntax version) is parsed into a query object.

2. **Translate to Generic Query (IR)**
   The query is converted into a platform-agnostic intermediate representation.

3. **Translate to Target Syntax**
   The IR is mapped into the target platform/version query model.

4. **Serialize**
   The new query object is serialized back into a query string.

5. **Validate**
   The upgraded query is re-parsed under the target syntax version to ensure syntactic validity.

This design ensures:

- **Maintainability**: one parser/translator/serializer per platform+version.
- **Consistency**: every upgrade path goes through the same IR.
- **Transparency**: lossy conversions trigger **warnings** instead of silent failures.
- **Extensibility**: adding a new syntax version or platform is linear work.
