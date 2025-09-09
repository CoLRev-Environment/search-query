Parser
============

Versioned parsers
-----------------

Parsers live in versioned modules such as
``search_query/pubmed/v1/parser.py``. Keeping previous versions
allows reproducible parsing and backward compatibility. See
`versioning policy <../platforms/syntax_upgrade.html#versioning-policy>`_ for details.

The central registry in ``search_query.parser`` exposes a ``PARSERS``
mapping and resolves the appropriate version at runtime. Calling
``parse(..., parser_version="latest")`` loads the highest available
version for the chosen platform.

When introducing a new parser version, copy the previous versioned
directory, adjust the implementation, and register the version in the
``PARSERS`` dictionary.

1. Inherit from base classes
-----------------------------------

Use the provided base classes, which provide a number of utility methods:

- ``QueryStringParser`` → for query strings
- ``QueryListParser`` → for numbered sub-query lists

2. Tokenization
-----------------------------------

Start by defining regex patterns for the different token types.

Recommended components::

    PARENTHESIS_REGEX = r"[\(\)]"
    LOGIC_OPERATOR_REGEX = r"\b(AND|OR|NOT)\b"
    PROXIMITY_OPERATOR_REGEX = r"NEAR/\d+"
    FIELD_REGEX = r"\b\w{2}="  # generic: like TI=, AB=
    TERM_REGEX = r"\"[^\"]+\"|\S+"

Join them into one pattern::

    pattern = "|".join([
        PARENTHESIS_REGEX,
        LOGIC_OPERATOR_REGEX,
        PROXIMITY_OPERATOR_REGEX,
        FIELD_REGEX,
        TERM_REGEX
    ])

.. note::
   Use a **broad** regex for field detection, and validate values later via the linter.

Implement ``tokenize()`` to assign token types and positions::

    for match in re.finditer(self.pattern, self.query_str):
        token = match.group().strip()
        start, end = match.span()

        if re.fullmatch(self.PARENTHESIS_REGEX, token):
            token_type = TokenTypes.PARENTHESIS_OPEN if token == "(" else TokenTypes.PARENTHESIS_CLOSED
        elif re.fullmatch(self.LOGIC_OPERATOR_REGEX, token):
            token_type = TokenTypes.LOGIC_OPERATOR
        else:
            token_type = TokenTypes.UNKNOWN

        self.tokens.append(Token(value=token, type=token_type, position=(start, end)))

Use or override ``combine_subsequent_terms()``:

.. code-block:: python

    self.combine_subsequent_terms()

To join adjacent tokens like ``data`` ``science`` → ``data science``.

3. Build the parse methods
-----------------------------------

Call the Linter to check for errors:

.. code-block:: python

    self.linter.validate_tokens()
    self.linter.check_status()

Add artificial parentheses (position: ``(-1,-1)``) to handle implicit operator precedence.

Implement ``parse_query_tree()`` to build the query object, creating nested queries for parentheses.

.. note::

    Parsers can be developed as top-down parsers (see PubMed) or bottom-up parsers (see Web of Science).

    For NOT operators, it is recommended to parse them as a query with two children. The second child is the negated part (i.e., the operator is interpreted as ``AND NOT``). For example, ``A NOT B`` should be parsed as:

    .. code-block:: python

        NOT[A, B]

Check whether ``SearchFields`` can be created for nested queries (e.g., ``TI=(eHealth OR mHealth)`` or only for individual terms, e.g., ``eHealth[ti] OR mHealth[ti]``.)

**Parser Skeleton**

.. literalinclude:: parser_skeleton.py
   :language: python


List format support
----------------------------------

Implement  ``QueryListParser`` to handle numbered sub-queries and references like ``#1 AND #2``.

.. note::

   To parse a list format, the numbered sub-queries should be replaced to create a search string, which can be parsed with the standard string-parser. This helps to avoid redundant implementation.
