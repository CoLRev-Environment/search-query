#!/usr/bin/env python
"""Generate field map for search-query"""
from tabulate import tabulate

from search_query.constants import Fields
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP


table = []
header = ["Fields"] + [pf for pf in PLATFORM]
for field in Fields.all():
    row = [field] + [PLATFORM_FIELD_MAP[syntax].get(field, "") for syntax in PLATFORM]
    table.append(row)

print(tabulate(table, headers=header))
