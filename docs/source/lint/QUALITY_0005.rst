.. _QUALITY_0005:

QUALITY_0005 — redundant-term
=============================

**Error Code**: QUALITY_0005

**Message**: ``Redundant term in the query``

**Problematic query (AND)**:

.. code-block:: text

    "digital health" AND "health"

**Recommended query (AND)**:

.. code-block:: text

    "digital health"

.. note::

    The term "digital health" is more specific than "health".
    The AND query will not retrieve results that match "health" but not "digital health".
    Therefore, the more specific term ("digital health") is sufficient.

**Problematic query (OR)**:

.. code-block:: text

    "digital health" OR "health"

**Recommended query (OR)**:

.. code-block:: text

    "health"

.. note::

    The term "health" is broader than "digital health".
    In the OR query, all results that match "digital health" will also match "health".
    Therefore, the broader term ("health") is sufficient.

**Typical fix**: Remove redundant terms that do not add value to the query.

**Back to**: :ref:`lint`
