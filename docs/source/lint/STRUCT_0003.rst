.. _STRUCT_0003:

STRUCT_0003 — boolean-operator-readability
==========================================

**Error Code**: STRUCT_0003

**Message**: ``Boolean operator readability``

**Problematic query**:

.. code-block:: text

    eHealth[ti] | mHealth[ti]

**Recommended query**:

.. code-block:: text

    eHealth[ti] OR mHealth[ti]

**Back to**: :ref:`lint`
