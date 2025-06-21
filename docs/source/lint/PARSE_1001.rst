.. _PARSE_1001:

PARSE_1001 — list-query-missing-root-node
=========================================

**Error Code**: PARSE_1001

**Message**: ``List format query without root node (typically containing operators)``

**Problematic query**:

.. code-block:: text

    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat" OR "acrobats")

**Recommended query**:

.. code-block:: text

    1. TS=("Peer leader*" OR "Shared leader*")
    2. TS=("acrobatics" OR "acrobat" OR "acrobats")
    3. #1 AND #2

**Typical fix**: Add a root-level operator to combine the list items into a single query.

**Back to**: :ref:`lint`
