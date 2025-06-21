.. _QUALITY_0002:

QUALITY_0002 — date-filter-in-subquery
======================================

**Error Code**: QUALITY_0002

**Message**: ``Date filter in subquery``

**Problematic query**:

.. code-block:: text

    (("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) AND 2019/01/01:2019/12/01[publication date]) OR ("ehealth"[Title/Abstract])
    device[ti] OR (wearable[ti] AND 2000:2010[dp])

**Recommended query**:

.. code-block:: text

    (("digital health"[Title/Abstract] AND "privacy"[Title/Abstract]) OR ("ehealth"[Title/Abstract])) AND 2019/01/01:2019/12/01[publication date]
    (device[ti] OR wearable[ti]) AND 2000:2010[dp]

**Typical fix**: Apply date filters at the top-level of the query instead of inside subqueries to ensure the date restriction applies as intended.

**Back to**: :ref:`lint`
