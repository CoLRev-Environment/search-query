.. _EBSCO_0001:

EBSCO_0001 — wildcard-unsupported
=================================

**Error Code**: EBSCO_0001

**Message**: ``Unsupported wildcard in search string.``

**Problematic query**:

.. code-block:: text

   # Leading wildcard
   TI=*Health

**Recommended query**:

.. code-block:: text

    TI=Health*

**Typical fix**:  Remove unsupported wildcard characters from the query.

**Back to**: :ref:`lint`
