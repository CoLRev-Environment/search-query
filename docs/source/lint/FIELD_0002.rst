.. _FIELD_0002:

FIELD_0002 — field-missing
==========================

**Error Code**: FIELD_0002

**Message**: ``Search field is missing``

**Problematic query**:

.. code-block:: text

    # PLATFORM.PUBMED:
    "eHealth" OR "digital health"

**Recommended query**:

.. code-block:: text

    # PLATFORM.PUBMED:
    "eHealth"[all] OR "digital health"[all]

**Back to**: :ref:`lint`
