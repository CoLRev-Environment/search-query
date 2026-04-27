.. _PARSE_1004:

PARSE_1004 — list-query-unreferenced-item
=========================================

**Error Code**: PARSE_1004

**Message**: ``Unreferenced line in list query``

**Problematic query**:

.. code-block:: text

    # PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat")
    3. #1

**Recommended query**:

.. code-block:: text

    # PLATFORM.WOS:
    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat")
    3. #1 AND #2

**Typical fix**: Reference all list items.

**Back to**: :ref:`lint`
