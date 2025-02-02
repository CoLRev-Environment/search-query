from search_query.linter import run_linter
from search_query.parser import parse
from search_query.search_file import SearchFile

# load File for parsing from path
search = SearchFile(
    "/home/ubuntu1/Thesis/example/ebscohost/10.1079_SEARCHRXIV.2022.00023.json"
)

# parse loaded file, depending on platform syntax written in File
query = parse(search.search_string, search.search_field_general, syntax=search.platform)

# while parsing is done, linter messages will be collected and printed here
messages = run_linter(
    search.search_string, search.search_field_general, syntax=search.platform
)
print(messages)
print("-" * 20)

# translates query string to syntax from ebsco host
ebsco_query = query.to_string(syntax="ebscohost")
print(ebsco_query)
