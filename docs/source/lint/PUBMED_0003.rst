.. _PUBMED_0003:

PUBMED_0003 — invalid-wildcard-use
==================================

**Error Code**: PUBMED_0003

**Message**: ``Invalid use of the wildcard operator *``

**Problematic query**:

.. code-block:: text

    "health tracking" AND AI*

**Recommended query**:

.. code-block:: text

    "health tracking" AND AID*

**Typical fix**: Avoid using wildcards (*) with short strings (less than 4 characters). Specify search fields directly in the query instead of relying on general search field settings.

**Back to**: :ref:`lint`
