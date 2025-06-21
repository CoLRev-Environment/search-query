.. _PARSE_0008:

PARSE_0008 — unsupported-prefix
===============================

**Error Code**: PARSE_0008

**Message**: ``Unsupported prefix in search query``

**Problematic query**:

.. code-block:: text

   Pubmed with no restrictions: (eHealth[ti])

**Recommended query**:

.. code-block:: text

    eHealth[ti]

**Typical fix**: Remove unsupported prefixes or introductory text from the search query to ensure it runs correctly.

**Back to**: :ref:`lint`
