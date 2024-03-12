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

To write the translated queries to a JSON file or print them, run:

```Python
query.write("translationIEEE.json", syntax="ieee")
query.write("translationPubMed.json", syntax="pubmed")
query.write("translationWebofScience.json", syntax="wos")

    or

query.to_string(syntax="ieee")
query.to_string(syntax="pubmed")
query.to_string(syntax="wos")

```

The `write()` methods create a JSON file using the parameter file name
The `to_string()` methods returns the translated string

## How to cite

Ernst, K. (2024). Towards more efficient literature search: Design of an open source query translator. Otto-Friedrich-University of Bamberg.

## Not what you're looking for?

This python package was developed with purpose of integrating it into other literature management tools. If that isn't your use case, it migth be useful for you to look at these related tools:

- LitSonar: https://litsonar.com/
- Polyglot: https://sr-accelerator.com/#/polyglot

## License

This project is distributed under the [MIT License](LICENSE).
