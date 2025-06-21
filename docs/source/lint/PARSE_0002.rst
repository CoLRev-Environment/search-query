.. _PARSE_0002:

PARSE_0002 — unbalanced-parentheses
===================================

**Error Code**: PARSE_0002

**Message**: ``Parentheses are unbalanced in the query``

**Problematic query**:

.. code-block:: text

    (a AND b OR c

**Recommended query**:

.. code-block:: text

    (a AND b) OR c

**Typical fix**: Check the parentheses in the query

**Back to**: :ref:`lint`
