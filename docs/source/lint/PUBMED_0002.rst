.. _PUBMED_0002:

PUBMED_0002 — character-replacement
===================================

**Error Code**: PUBMED_0002

**Message**: ``Character replacement``

**Problematic query**:

.. code-block:: text

    "healthcare" AND "Industry 4.0"

**Recommended query**:

.. code-block:: text

    "healthcare" AND "Industry 4 0"

**Typical fix**: Be aware that certain characters like . in search terms will be replaced with whitespace due to platform-specific conversions. Specify search fields explicitly within the query instead of relying on general settings.

**Back to**: :ref:`lint`
