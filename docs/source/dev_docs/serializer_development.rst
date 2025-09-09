Serializer
===========

Serializers convert a query object into a string representation.
This enables the query to be rendered for human inspection, logging, or submission to search engines.

Each serializer implements a function that takes a `Query` object and returns a string.
This supports various output formats including debugging views and platform-specific syntaxes.

Interface
---------
Serializers are typically implemented as standalone functions. The core interface is:

.. literalinclude:: serializer_skeleton.py
   :language: python

Serializers follow a shared conceptual pattern:

- Accept a `Query` object.
- Recursively traverse the query tree.
- Render each node (logical operator, term, field) into a string.
- Combine child nodes with appropriate formatting and syntax.

.. note::

  Avoid embedding platform-specific validation logic (use linters for that).

Versioned serializers
---------------------

Serializers live in versioned modules such as
``search_query/pubmed/v1/serializer.py``. See
`versioning policy <../platforms/syntax_upgrade.html#versioning-policy>`_ for details.

They are registered in the
central ``search_query.serializer`` module via the ``SERIALIZERS``
mapping. ``LATEST_SERIALIZERS`` resolves the latest version at
runtime when no explicit ``serializer_version`` is provided.

Example stored query with version information:

.. code-block:: json

   {
       "platform": "wos",
       "search_string": "TS=(quantum dot)",
       "version": "1"
   }
