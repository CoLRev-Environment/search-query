Linter
============

The linter checks should reuse (or extend) the messages from the constants module, which are documented in the `messages <../messages/errors_index.html>`_ section.
The linter message should be unambiguously defined in the constants module.
An additional *details* parameter can be added to the linter message, explaining the specific problem.

.. literalinclude:: linter_skeleton.py
   :language: python


Search Field Validation
-------------------------

Strict vs. Non-Strict Modes

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
