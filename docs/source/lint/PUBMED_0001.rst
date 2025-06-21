.. _PUBMED_0001:

PUBMED_0001 — nested-query-with-field
=====================================

**Error Code**: PUBMED_0001

**Message**: ``A Nested query cannot have a search field.``

**Problematic query**:

.. code-block:: text

    eHealth[ti] AND ("health tracking" OR "remote monitoring")[tiab]

**Recommended query**:

.. code-block:: text

    eHealth[ti] AND ("health tracking"[tiab] OR "remote monitoring"[tiab])

**Typical fix**: Remove the search field from the nested query (operator) since nested queries cannot have search fields.

**Back to**: :ref:`lint`
