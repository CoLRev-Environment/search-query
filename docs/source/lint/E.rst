.. _E:

E — search-field-implicit
=========================

**Error Code**: E

**Message**: ``Search field is implicitly specified``

**Scope**: all

**Problematic query**:

.. code-block:: text

    # PLATFORM.PUBMED:

    "eHealth" OR "digital health"

**Recommended query**:

.. code-block:: text

    # PLATFORM.PUBMED:

    "eHealth"[all] OR "digital health"[all]

**Typical fix**: Explicitly specify the search field in the query string instead of relying on a general search field setting.

**Back to**: :ref:`lint`
