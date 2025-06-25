.. _QUALITY_0004:

QUALITY_0004 — unnecessary-parentheses
======================================

**Error Code**: QUALITY_0004

**Message**: ``Unnecessary parentheses in queries``

**Problematic query**:

.. code-block:: text

    ("digital health" OR "eHealth") OR ("remote monitoring" OR "telehealth")

**Recommended query**:

.. code-block:: text

    "digital health" OR "eHealth" OR "remote monitoring" OR "telehealth

**Explanation**: Parentheses are unnecessary when all operators used are **associative and have equal precedence** (like a series of ORs or a series of ANDs). In such cases, the grouping does not influence the evaluation result and adds unnecessary complexity.

**Back to**: :ref:`lint`
