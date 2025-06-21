.. _PARSE_0009:

PARSE_0009 — unsupported-suffix
===============================

**Error Code**: PARSE_0009

**Message**: ``Unsupported suffix in search query``

**Problematic query**:

.. code-block:: text

   (eHealth[ti]) Sort by: Publication Date

**Recommended query**:

.. code-block:: text

    (eHealth[ti])

**Typical fix**: Remove unsupported suffixes or trailing text from the search query to avoid errors.

**Back to**: :ref:`lint`
