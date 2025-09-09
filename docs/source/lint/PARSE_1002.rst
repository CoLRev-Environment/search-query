.. _PARSE_1002:

PARSE_1002 — list-query-invalid-reference
=========================================

**Error Code**: PARSE_1002

**Message**: ``Invalid list reference in list query``

**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat")
    3. #1 AND #5

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat")
    3. #1 AND #2

**Typical fix**: Reference only existing list items.

**Back to**: :ref:`lint`
