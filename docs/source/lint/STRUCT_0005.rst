.. _STRUCT_0005:

STRUCT_0005 — search-term-lowercase
===================================

**Error Code**: STRUCT_0005

**Message**: ``Unquoted search terms should be lowercase``

**Problematic query**:

.. code-block:: text

    VR AND game

**Recommended query**:

.. code-block:: text
    
    vr AND game

**Typical fix**: Make unquoted search term lowercase

**Back to**: :ref:`lint`
