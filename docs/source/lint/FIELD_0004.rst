.. _FIELD_0004:

FIELD_0004 — field-implicit
===========================

**Error Code**: FIELD_0004

**Message**: ``Search field is implicitly specified``

**Problematic query**:

.. code-block:: text

    # PLATFORM.PUBMED:

    "eHealth" OR "digital health"

**Recommended query**:

.. code-block:: text

    # PLATFORM.PUBMED:

    "eHealth"[all] OR "digital health"[all]

**Typical fix**: Explicitly specify the search field in the query string instead of relying on a general search field setting.

**Back to**: :ref:`lint`
