Tests
============

This section outlines best practices for writing unit tests in the `search_query` package.
Tests are primarily written using `pytest` and are organized by module (`parser`, `linter`, `translator`, etc.).


To run all tests:
::

    pytest test

Test types
----------

1. **Tokenization Tests**
    - Purpose: Verify that a query string is tokenized correctly into expected tokens.
    - Tools: `pytest.mark.parametrize` for multiple cases.
    - Example:

   .. code-block:: python

            @pytest.mark.parametrize(
               "query_str, expected_tokens",
               [
                  (
                        "AB=(Health)",
                        [
                           Token(value="AB=", type=TokenTypes.FIELD, position=(0, 3)),
                           Token(value="(", type=TokenTypes.PARENTHESIS_OPEN, position=(3, 4)),
                           Token(value="Health", type=TokenTypes.TERM, position=(4, 10)),
                           Token(value=")", type=TokenTypes.PARENTHESIS_CLOSED, position=(10, 11)),
                        ],
                  )
               ],
            )
            def test_tokenization(query_str: str, expected_tokens: list) -> None:
               print(
                  f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
               )

               parser = XYParser(query_str)
               parser.tokenize()

               assert parser.tokens == expected_tokens, (
                  f"\nExpected: {expected_tokens}\nGot     : {parser.tokens}"
               )

2. **Linter Message Tests**
    - Purpose: Verify that the linter raises expected warnings or errors for malformed input.
    - Approach:
      - Catch exceptions where necessary.
      - Use structured comparison with linter messages.
    - Example:

   .. code-block:: python

         @pytest.mark.parametrize(
            "query_str, field_general, messages",
            [
               (
                     '("health tracking" OR "remote monitoring") AND (("mobile application" OR "wearable device")',
                     "Title",
                     [
                        {
                           "code": "PARSE_0002",
                           "label": "unbalanced-parentheses",
                           "message": "Parentheses are unbalanced in the query",
                           "is_fatal": True,
                           "position": (47, 48),
                           "details": "Unbalanced opening parenthesis",
                        },
                        {
                           "code": "FIELD_0002",
                           "label": "field-missing",
                           "message": "Expected search field is missing",
                           "is_fatal": False,
                           "position": (-1, -1),
                           "details": "Search fields should be specified in the query instead of the field_general",
                        },
                     ],
               ),
               # add more cases here as needed...
            ],
         )
         def test_linter(query_str: str, field_general: str, messages: list[dict]) -> None:

            parser = XYParser(query_str, field_general=field_general)
            try:
               parser.parse()
            except SearchQueryException:
               pass  # Errors are expected in some cases

            actual_messages = parser.linter.messages
            if actual_messages != messages:
               print("Expected:")
               for m in messages:
                     print(f"  - {m}")
               print("Got:")
               for m in actual_messages:
                     print(f"  - {m}")

            assert actual_messages == messages

3. **Translation Tests**
    - Purpose: Confirm that parsing + serialization results in the expected generic or structured query string.

Example:

.. code-block:: python

   @pytest.mark.parametrize(
      "query_string, expected_translation",
      [
            ("TS=(eHealth) AND TS=(Review)",
            "AND[eHealth[TS=], Review[TS=]]"),
      ],
   )
   def test_parser_translation(query_string, expected_translation):
      parser = XYParser(query_string)
      query_tree = parser.parse()
      assert query_tree.to_generic_string() == expected_translation


.. note::

   - Use helper functions like `parser.print_tokens()` to ease debugging.
   - Use `assert ... == ...` with fallbacks for `print(...)` for inspection.

4. **Golden File Tests**
    - Purpose: Ensure that parsing and serialization remain stable across
      versions. Store expected outputs as versioned "golden" files and
      compare test results against them.

5. **Deprecated Syntax Tests**
    - Purpose: Verify that linters flag outdated constructs using
      the deprecated syntax message (``LINT_2001``).
    - Example:

   .. code-block:: python

      def test_deprecated_operator():
         parser = XYParser('term1 SAME term2')
         parser.parse()
         assert any(m['code'] == 'LINT_2001' for m in parser.linter.messages)
