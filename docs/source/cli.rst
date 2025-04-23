.. _cli:

CLI
==========================================================

The CLI reads a query from an input file, converts it from a specified source format
to a target format, and writes the converted query to an output file.

To translate a search query on the command line, run

.. code-block:: bash

    search-query-translate --from colrev_web_of_science \
                            --input input_query.txt \
                            --to colrev_pubmed \
                            --output output_query.txt

**Arguments**

- ``--from`` (required):
  The source query format.
  Example: ``colrev_web_of_science``

- ``--input`` (required):
  Path to the input file containing the original query.

- ``--to`` (required):
  The target query format.
  Example: ``colrev_pubmed``

- ``--output`` (required):
  Path to the file where the converted query will be written.


**Example**

Suppose you have a Web of Science search query saved in ``input_query.txt`` and you want to convert it to a PubMed-compatible format. Run:

.. code-block:: bash

    search-query-translate --from colrev_web_of_science \
                            --input input_query.txt \
                            --to colrev_pubmed \
                            --output output_query.txt

The converted query will be saved in ``output_query.txt``.

Linters can be run on the CLI:

.. code-block:: bash

    search-query-lint search-file.json
