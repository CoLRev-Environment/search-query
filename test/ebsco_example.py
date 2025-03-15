#!/usr/bin/env python
"""Example for search query translation and construction."""
from search_query.and_query import AndQuery
from search_query.linter import run_linter
from search_query.or_query import OrQuery
from search_query.parser import parse
from search_query.save_file import SaveFile
from search_query.search_file import SearchFile

####################################################################################
# This part is an example on how to load an existing query
# from an existing json file and translate it to the ebsco format
####################################################################################

# Load File for parsing from path
search = SearchFile(
    "/home/ubuntu1/Thesis/example/ebscohost/10.1079_SEARCHRXIV.2022.00023.json"
)

# Parse loaded file, depending on platform syntax written in File
query = parse(search.search_string, search.search_field_general, syntax=search.platform)

# While parsing is done, linter messages will be collected and printed here
messages = run_linter(
    search.search_string, search.search_field_general, syntax=search.platform
)
print(messages)
print("-" * 20)

# Translates query string to syntax from ebsco host
ebsco_query = query.to_string(syntax="ebscohost")
print(ebsco_query)


####################################################################################
# This part is an example on how to build your own query
# and save it to a json file
####################################################################################

# To build your own query use building blocks like this:
digital_synonyms = OrQuery(["digital", "virtual", "online"], search_field="ti")
work_synonyms = OrQuery(["work", "labor", "service"], search_field="ab")
new_query = AndQuery([digital_synonyms, work_synonyms], search_field="")

# Translate from standard pre-notation to ebsco format
new_ebsco_query = new_query.to_string("ebscohost")
print(new_ebsco_query)


# To safe query into json file run this code:
# These variable must be set before running the script
coder_initials = "TF"
parent_directory = "/home/ubuntu1/Thesis/new_queries/"
filename = "test-ebsco-string.json"
syntax = "ebscohost"
platform = "EBSCOhost"
authors = [{"name": "Thomas Fleischmann"}]
comment = ""  # Comments are optional


# No changes necessary here
new_file = SaveFile(
    filename=filename,
    query_str=new_ebsco_query,
    syntax=syntax,
    platform=platform,
    authors=authors,
    parent_directory=parent_directory,
    coder_initials=coder_initials,
    comment=comment,
)
new_file.save()
