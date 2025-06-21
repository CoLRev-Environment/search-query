.. _STRUCT_0004:

STRUCT_0004 — invalid-proximity-use
===================================

**Error Code**: STRUCT_0004

**Message**: ``Invalid use of the proximity operator``

Proximity operators must have a non-negative integer as the distance.

**Problematic query**:

.. code-block:: text

    "digital health"[tiab:~0.5]

**Recommended query**:

.. code-block:: text

    "digital health"[tiab:5]

**Back to**: :ref:`lint`
