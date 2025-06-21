.. _QUALITY_0003:

QUALITY_0003 — journal-filter-in-subquery
=========================================

**Error Code**: QUALITY_0003

**Message**: ``Journal (or publication name) filter in subquery``

**Problematic query**:

.. code-block:: text

    "activity"[Title/Abstract] OR ("cancer"[Title/Abstract] AND "Lancet"[Journal])

**Recommended query**:

.. code-block:: text

    ("activity"[Title/Abstract] OR "cancer"[Title/Abstract]) AND "Lancet"[Journal]

**Typical fix**: Apply journal (publication name) filters at the top level of the query instead of inside subqueries to ensure the filter applies to the entire result set.

**Back to**: :ref:`lint`
