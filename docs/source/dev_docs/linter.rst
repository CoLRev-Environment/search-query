Linter development
=====================

Parser modes
----------------

**Strict mode**: Forces the user to maintain clean, valid input but at the cost of convenience.

- Fails on fatal or error outcomes. Prints warnings.

**Non-strict mode**: Focuses on usability, automatically resolving common issues while maintaining transparency via warnings.

- Fails only on fatal outcomes. Auto-corrects errors as much as possible and prints a message (adds a fatal message if this is not possible). Prints warnings.

An additional "silent" option may be used to silence warnings.

Messages
-----------------

The parser/linter can add different messages (level: fatal, error, warning). Initial examples for the messages are:

**Fatal**

- tokenizing-failed (F0001)
- unbalanced-parentheses (F0002)
- missing-operator (F0003)

**Error**

- search-field-contradiction (E0001)
- search-field-missing (E0002)
- search-field-unsupported (E0003)

**Warning**

- search-field-redundant (W0001), description: recommend specifying search-field in the search string only
- search-field-extracted (W0002), description: recommend specifying search-field in the search string
- search-field-not-specified (W0003), description: search-field should be specified explicitly
- query-structure-unnecessarily-complex (W0004), description: example "big data" AND (data AND (quality OR error OR problem)) would be equivalent to: "big data" AND (quality OR error OR problem)

Search Field Validation in Strict vs. Non-Strict Modes
----------------------------------------------------------

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


Resources
---------------

- `Web of Science Errors <https://images.webofknowledge.com/WOKRS528R6/help/TCT/ht_errors.html>`_
