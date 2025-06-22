Linter
============

Linters are responsible for validating query strings or query lists before execution.
They analyze token sequences, syntax, search fields, and operator use to identify
errors or ambiguities and print meaningful messages (documented in the `messages <../messages/errors_index.html>`_ section).
Each platform implements its own linter, which interhits from the base class `linter_base.py`. Linters are used in the parser methods.

Base Classes
------------
Use the appropriate base class when developing a new linter:

- `QueryStringLinter`: for single query strings
- `QueryListLinter`: for list-based query formats

Each linter must override the `validate_tokens()` method and the `validate_query_tree()`.
`validate_tokens()` is called when the query is parsed, and `validate_query_tree()` is called when the query tree is built (i.e., at the end of the parsing process **and** when the query is constructed programmatically).

Best Practices
--------------
- **Use standardized linter messages** defined in `constants.QueryErrorCode`.
- **Add details** in messages for user guidance (e.g., invalid format, missing logic).
- Ensure **valid token sequences** using the `VALID_TOKEN_SEQUENCES` dictionary.
- Consider using **utility methods** provided by `linter_base.py`:
  - `check_unbalanced_parentheses()`
  - `check_unknown_token_types()`
  - `add_artificial_parentheses_for_operator_precedence()`
  - `check_invalid_characters_in_term(chars)`
  - `check_operator_capitalization()`
  - etc.
- For **search field validation**, use a corresponding field mapping and helper functions like `map_to_standard()`.

.. literalinclude:: linter_skeleton.py
   :language: python
