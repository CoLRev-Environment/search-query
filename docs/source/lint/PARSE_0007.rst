.. _PARSE_0007:

PARSE_0007 — query-in-quotes
============================

**Error Code**: PARSE_0007

**Message**: ``The whole Search string is in quotes.``

**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS
    "eHealth[ti] AND digital health[ti]"

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS
    eHealth[ti] AND digital health[ti]

**Back to**: :ref:`lint`
