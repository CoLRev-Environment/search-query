.. _PARSE_0006:

PARSE_0006 — invalid-syntax
===========================

**Error Code**: PARSE_0006

**Message**: ``Query contains invalid syntax``

**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS
    eHealth[ti]

    # PLATFORM.PUBMED
    TI=eHealth

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS
    TI=eHealth

    # PLATFORM.PUBMED
    eHealth[ti]

**Back to**: :ref:`lint`
