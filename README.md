#  Welcome!

This python package was developed as part of my bachelors thesis: Towards more efficient literature search: Design of an open source query translator.

How to cite: 
Ernst, K. (2024). Towards more efficient literature search: Design of an open source query translator. Otto-Friedrich-University of Bamberg.

# How to use?

A python package for the translation of literature search queries.

To create queries, run:

```
import search_query.query

nested_query = search_query.query.OrQuery(["index", "search"], [], "Abstract")
query = search_query.query.AndQuery(["terms"], [nested_query], "Author Keywords")
```
search terms: strings which you want to include in the search query
nested queries: queries whose roots are appended to the query
search field: search field to which the query should be applied
  -> possible are: Author Keywords, Abstract, Author, DOI, ISBN, Publisher or Title

to use the translation function, run:

```
query.translate_ieee("translationIEEE") 
query.translate_pubmed("translationPubMed")
query.translate_wos("translationWebofScience")

    or

query.print_query_ieee(query.query_tree.root)
query.print_query_pubmed(query.query_tree.root)
query.print_query_wos(query.query_tree.root)

```
The translate() methods create a JSON file in the "translations/databaseName/" directory under the stated file name
The print() methods returns just the translated string

# Not what you're looking for?

This python package was developed with purpose of integrating it into other literature management tools. If that isn't your use case, it migth be useful for you to look at these related tools:

- LitSonar: https://litsonar.com/
- Polyglot: https://sr-accelerator.com/#/polyglot 

