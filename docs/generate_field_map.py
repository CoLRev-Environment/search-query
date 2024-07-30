#!/usr/bin/env python
"""Generate field map for search-query"""
from tabulate import tabulate

from search_query.constants import DB
from search_query.constants import DB_FIELD_MAP
from search_query.constants import Fields


table = []
header = ["Fields"] + [db for db in DB]
for field in Fields.all():
    row = [field] + [DB_FIELD_MAP[syntax].get(field, "") for syntax in DB]
    table.append(row)

print(tabulate(table, headers=header))
