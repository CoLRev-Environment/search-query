Translator
============

Translators convert between:

- Generic query syntax used in internal logic, and
- Specific query syntax required by a given search engine (e.g., PubMed, EBSCO, Web of Science).

Each translator implements `QueryTranslator`, the abstract base class from ``translator_base.py``.

Translator responsibilities
--------------------------

A translator must implement the following two class methods:

- ``to_generic_syntax(query, *, field_general) -> Query``
- ``to_specific_syntax(query) -> Query``

Each method receives a `Query` object (the internal AST) and must return a new `Query` object with appropriately translated search fields and structure.

Versioned translators
-------------------------

Translators are organized in versioned modules such as
``search_query/pubmed/v1/translator.py``. See
`versioning policy <../platforms/syntax_upgrade.html#versioning-policy>`_ for details.
This structure preserves older versions,
enabling reproducible translations and ensuring backward compatibility.

A central registry in ``search_query.translator`` provides a ``TRANSLATORS`` mapping,
which dynamically selects the appropriate translator version at runtime. Invoking
``translate(..., translator_version="latest")`` loads the most recent version for the
specified platform.

To introduce a new translator version, duplicate the previous versioned directory,
update the implementation as needed, and register the new version in the ``TRANSLATORS`` dictionary.

Utility methods provided
-----------------------

The base class (`QueryTranslator`) provides the following utilities:

- ``move_field_from_operator_to_terms(query)``:
  Moves a shared search field from the operator level to each child query.
- ``flatten_nested_operators(query)``:
  Merges nested logical operators of the same type into a flat structure.
- ``move_fields_to_operator(query)``:
  If all children have the same field, moves it to the parent node.

Search field mapping
-------------------

Field mapping is expected to be defined in a `constants_<source>.py` file and typically includes:

- ``syntax_str_to_generic_field_set()``: maps specific syntax string (e.g., `TI`, `AB`) to **set of generic `Fields`**. When the set contains multiple elements, the query must be extended with OR (see PubMed translator: ``_expand_combined_fields()``).
- ``generic_field_to_syntax_field()``: maps generic `Fields` to platform-specific syntax (set of fields). When combined fields are available, the query must be adapted before (see PubMed tranlsator: ``_combine_tiab()``).

Each translator should:

1. Translate fields in both directions
2. Handle combined fields (e.g., `[tiab]` in PubMed)
3. Optionally restructure the query for consistency

Code skeleton
------------

.. literalinclude:: translator_skeleton.py
   :language: python


Advanced features
----------------

Some translators include advanced restructuring logic:

- **PubMed**: supports `[tiab]` expansion into OR combinations of `[ti]` and `[ab]`
