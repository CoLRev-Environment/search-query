#!/usr/bin/env python
"""Generate field map for search-query"""
from tabulate import tabulate

from search_query.constants import Fields
from search_query.constants import Syntax
from search_query.constants import SYNTAX_FIELD_MAP


table = []
header = ["Fields"] + [syntax for syntax in Syntax]
for field in Fields.all():
    row = [field] + [SYNTAX_FIELD_MAP[syntax].get(field, "") for syntax in Syntax]
    table.append(row)

print(tabulate(table, headers=header))
