.. _FIELD_0001:

FIELD_0001 — field-unsupported
==============================

**Error Code**: FIELD_0001

**Message**: ``Search field is not supported for this database``

**Problematic query**:

.. code-block:: text

    TI=term1 AND IY=2020

**Recommended query**:

.. code-block:: text

    TI=term1 AND PY=2020

**Typical fix**: Replace the unsupported field with a supported one for the selected database.

**Back to**: :ref:`lint`
