#  Welcome to search-query

Search-query is a Python package to translate literature search queries across databases, such as PubMed and Web of Science.
This package was developed as part of my Bachelor's thesis: Towards more efficient literature search: Design of an open source query translator.

## How to use?

To create queries, run:

```Python
from search_query import OrQuery, AndQuery

nested_query = OrQuery(["index", "search"], [], "Abstract")
query = AndQuery(["terms"], [nested_query], "Author Keywords")
```

Parameters:

- search terms: strings which you want to include in the search query,
- nested queries: queries whose roots are appended to the query,
- search field: search field to which the query should be applied (avaliable options: `Author Keywords`, `Abstract`, `Author`, `DOI`, `ISBN`, `Publisher` or `Title`)

To use the translation function, run:

```Python
query.translate_ieee("translationIEEE")
query.translate_pubmed("translationPubMed")
query.translate_wos("translationWebofScience")

    or

query.print_query_ieee(query.query_tree.root)
query.print_query_pubmed(query.query_tree.root)
query.print_query_wos(query.query_tree.root)

```

The `translate()` methods create a JSON file in the "translations/databaseName/" directory under the stated file name
The `print()` methods returns just the translated string

## How to cite

Ernst, K. (2024). Towards more efficient literature search: Design of an open source query translator. Otto-Friedrich-University of Bamberg.

## Not what you're looking for?

This python package was developed with purpose of integrating it into other literature management tools. If that isn't your use case, it migth be useful for you to look at these related tools:

- LitSonar: https://litsonar.com/
- Polyglot: https://sr-accelerator.com/#/polyglot

## License

This project is distributed under the [MIT License](LICENSE).
