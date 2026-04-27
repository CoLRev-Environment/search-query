.. _PARSE_1003:

PARSE_1003 — list-query-circular-reference
==========================================

**Error Code**: PARSE_1003

**Message**: ``Query line references itself``

**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat")
    3. #1 AND #2 AND #3

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat")
    3. #1 AND #2

**Typical fix**: Remove the circular reference.

**Back to**: :ref:`lint`
