.. _cli:

CLI
==========================================================

The CLI reads a query from an input file, converts it from a specified source format
to a target format, and writes the converted query to an output file.

To translate a search query on the command line, run

.. code-block:: bash

    search-query translate --input input_query.json \
                            --to pubmed \
                            --output output_query.json

**Arguments**

- ``--input`` (required):
  Path to the input file containing the original query.

- ``--to`` (required):
  The target query format.
  Example: ``pubmed``

- ``--output`` (required):
  Path to the file where the converted query will be written.

The format of the ``input_query.json`` is stored in the ``platform`` field of the JSON file.

Linters can be run on the CLI:

.. code-block:: bash

    search-query lint search-file.json
