.. _FIELD_0003:

FIELD_0003 — field-extracted
============================

**Error Code**: FIELD_0003

**Message**: ``Recommend explicitly specifying the search field in the string``

**Problematic query**:

.. code-block:: text

    # EBSCO search with general search field = "Title"
    Artificial Intelligence AND Future

**Recommended query**:

.. code-block:: text

    # EBSCO search without general search field
    TI Artificial Intelligence AND TI Future

**Typical fix**: Explicitly specify the search fields in the query string rather than relying on a general search field setting. (EBSCO)

**Rationale**: The search_string may be copied and the general_field missed, leading to incorrect reproduction of the query.

**Back to**: :ref:`lint`
