Serializers
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
