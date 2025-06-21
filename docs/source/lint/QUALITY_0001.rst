.. _QUALITY_0001:

QUALITY_0001 — query-structure-unnecessarily-complex
====================================================

**Error Code**: QUALITY_0001

**Message**: ``Query structure is more complex than necessary``

**Problematic query**:

.. code-block:: text

    # PLATFORM.EBSCO
    TI "sleep" OR TI "sleep disorders"

    # PLATFORM.EBSCO
    TI "sleep" AND TI "sleep disorders"


**Recommended query**:

.. code-block:: text

    # PLATFORM.EBSCO
    TI "sleep"

    # PLATFORM.EBSCO
    TI "sleep disorders"


**Typical fix**: Remove redundant terms when one term is already covered by a broader (OR) or encompassing (AND) term in the query.

**Back to**: :ref:`lint`
