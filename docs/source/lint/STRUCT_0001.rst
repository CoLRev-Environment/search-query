.. _STRUCT_0001:

STRUCT_0001 — implicit-precedence
=================================

**Error Code**: STRUCT_0001

**Message**: ``Operator changed at the same level (explicit parentheses are recommended)``

**Problematic query**:

.. code-block:: text

    # PLATFORM.PUBMED
   "health tracking" OR ("remote" AND "monitoring") AND ("mobile application" OR "wearable device")

**Recommended query**:

.. code-block:: text

    # PLATFORM.PUBMED
    ("health tracking" OR ("remote" AND "monitoring")) AND ("mobile application" OR "wearable device")

**Typical fix**: Use explicit parentheses to clarify operator precedence and avoid ambiguity in mixed AND/OR queries.

**Back to**: :ref:`lint`
