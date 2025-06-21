.. _PARSE_0003:

PARSE_0003 — unbalanced-quotes
==============================

**Error Code**: PARSE_0003

**Message**: ``Quotes are unbalanced in the query``

**Problematic query**:

.. code-block:: text

    "eHealth[ti]

**Recommended query**:

.. code-block:: text

    "eHealth"[ti]

**Typical fix**: Add the missing closing quote to balance the quotation marks.

**Back to**: :ref:`lint`
