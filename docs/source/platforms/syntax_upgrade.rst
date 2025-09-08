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

To upgrade a query stored in ``query.json`` to version ``2.0.0`` of a given database syntax:

.. code-block:: console

   search-query upgrade query.json --to 2.0.0

If ``--to`` is omitted or set to ``latest``, the tool automatically selects
the latest syntax version for the specified database.
The upgraded query will be written back to the file (or another location if
specified with ``--output``).

.. note::

   **What does "syntax version" mean?**

   A *syntax version* identifies the **evolving query language of a database platform**
   (e.g., PubMed, Web of Science), not the version of this package.

   The latest package version (of ``search-query``) evolves independently and
   contains the most up-to-date parser/translator/serializer for the syntax versions it supports
   across databases.

Key Concepts
------------

- **Database Syntax Version (DSV)**
  The identifier of the query language as implemented by a database provider
  (e.g., supported operators, search fields, precedence rules).

- **Package Platform Version**
  The version of the local ``search-query`` package/connector.
  It may increment independently from database syntax versions.
  New package releases can improve or extend support for *existing* DSVs
  without implying that the database syntax itself changed.

- **Observability**
  Discoverability and testability of a DSV in the wild.
  Observability of *historic* versions is often limited because providers rarely
  document all changes systematically.
  What matters most is that the **current/latest DSV is observable** (i.e., can be tested)
  and that **material evolutions** in a database’s syntax can be recognized.

Versioning Policy
-----------------

Version identifiers follow a pragmatic schema aligned with semantic versioning,
with emphasis on **MAJOR** and **MINOR** to reflect real-world database syntax evolution:

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

   1. store queries in the **current DSV**,
   2. **upgrade** them to a newer DSV when available, and
   3. **anticipate** that the database syntax may evolve (occasionally via new MAJOR versions).

   Full support for arbitrarily many **historic** DSVs
   (including fine-grained distinctions and *backward* translation) is **not** a primary goal.
   Database Syntax Versions (DSV) start with 1.0 as of 2025-09-01. Previous versions will not be
   explored systematically and version 0.0 may be used as a placeholder for all previous syntax versions.

Observability of Syntax Versions
--------------------------------

Database providers do not always publish precise, comprehensive changelogs of syntax rules. As a result:

- Old DSVs may be only partially reconstructable.
- The focus is ensuring the **latest/current DSV** is well covered and testable.
- When a significant change is detected, the package encodes it as a new DSV and
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
   The upgraded query is re-parsed under the target DSV to ensure syntactic validity.

This design ensures:

- **Maintainability**: one parser/translator/serializer per platform+version.
- **Consistency**: every upgrade path goes through the same IR.
- **Transparency**: lossy conversions trigger **warnings** instead of silent failures.
- **Extensibility**: adding a new syntax version or platform is linear work.

Primary Use Cases
-----------------

- **Normalize to current**: Store queries in the latest/current DSV for future-proofness.
- **Upgrade forward**: Move queries to newer DSVs as they are introduced.
- **Guard against change**: Recognize and test for breaking evolutions (MAJOR)
  when database providers update their syntax.

Limitations & Non-Goals
-----------------------

- **Comprehensive backward translation** into historical DSVs is not guaranteed.
- **Perfect reconstruction** of undocumented, legacy syntax is often infeasible.
- Where conversions are **lossy** (e.g., target lacks a feature), the tool issues explicit warnings.

FAQ
---

**Q: Why separate database syntax versions from the package version?**

A: Because database providers may evolve their query languages.
The package updates to track those changes and to improve tooling—
even when the database syntax remains the same.

**Q: What if a database silently changes behavior?**

A: The project treats detectable, material changes as a new DSV
and routes upgrades through the IR.
Tests for the latest/current DSV ensure observability.

**Q: Can I pin to an older DSV?**

A: You can keep metadata that records the DSV used when a query was authored.
Upgrading is recommended when a newer DSV becomes available and observable.
