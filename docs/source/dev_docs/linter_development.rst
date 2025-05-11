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

Each linter must override the `validate_tokens()` method and optionally `validate_query_tree()` for deeper semantic checks.

Best Practices
--------------
- **Use standardized linter messages** defined in `constants.QueryErrorCode`.
- **Add details** in messages for user guidance (e.g., invalid format, missing logic).
- Ensure **valid token sequences** using the `VALID_TOKEN_SEQUENCES` dictionary.
- Consider using **utility methods** provided by `linter_base.py`:
  - `check_unbalanced_parentheses()`
  - `check_unknown_token_types()`
  - `add_artificial_parentheses_for_operator_precedence()`
  - `check_invalid_characters_in_search_term(chars)`
  - `check_operator_capitalization()`
  - etc.
- For **search field validation**, use a corresponding field mapping and helper functions like `map_to_standard()`.

.. literalinclude:: linter_skeleton.py
   :language: python


Strict vs. Non-Strict Mode
---------------------------

In non-strict mode (`mode="lenient"`), linters report errors but do not raise exceptions.
In strict mode (`mode="strict"`), any linter message will cause an exception to be raised,
which can be used for automated pipelines or validation gates.

Field validation in strict vs. non-strict modes

.. list-table:: Search Field Validation in Strict vs. Non-Strict Modes
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - **Search-Field required**
     - **Search String**
     - **Search-Field**
     - **Mode: Strict**
     - **Mode: Non-Strict**
   * - Yes
     - With Search-Field
     - Empty
     - ok
     - ok
   * - Yes
     - With Search-Field
     - Equal to Search-String
     - ok - search-field-redundant
     - ok
   * - Yes
     - With Search-Field
     - Different from Search-String
     - error: search-field-contradiction
     - ok - search-field-contradiction. Parser uses Search-String per default
   * - Yes
     - Without Search-Field
     - Empty
     - error: search-field-missing
     - ok - search-field-missing. Parser adds `title` as the default
   * - Yes
     - Without Search-Field
     - Given
     - ok - search-field-extracted
     - ok
   * - No
     - With Search-Field
     - Empty
     - ok
     - ok
   * - No
     - With Search-Field
     - Equal to Search-String
     - ok - search-field-redundant
     - ok
   * - No
     - With Search-Field
     - Different from Search-String
     - error: search-field-contradiction
     - ok - search-field-contradiction. Parser uses Search-String per default
   * - No
     - Without Search-Field
     - Empty
     - ok - search-field-not-specified
     - ok - Parser uses default of database
   * - No
     - Without Search-Field
     - Given
     - ok - search-field-extracted
     - ok
