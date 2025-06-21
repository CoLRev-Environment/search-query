.. _PARSE_0004:

PARSE_0004 — invalid-token-sequence
===================================

**Error Code**: PARSE_0004

**Message**: ``The sequence of tokens is invalid.``

**Problematic query**:

.. code-block:: texts

    # Example: Two operators in a row
    eHealth AND OR digital health

**Recommended query**:

.. code-block:: text

    eHealth OR digital health

**Typical fix**: Check the sequence of operators and terms in the query

**Back to**: :ref:`lint`
