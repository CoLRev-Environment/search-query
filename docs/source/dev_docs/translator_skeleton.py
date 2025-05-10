import re

# handle special cases before (e.g., [tiab:~6])?
# simply replace the search_field values

# Map different variations (such as capitalization, short/long versions) to a standard_syntax_str
PREPROCESSING_MAP = {
    "TI=": r"TI=|Title=",
}

def map_to_standard(syntax_str: str) -> set:
    for standard_key, variation_regex in PREPROCESSING_MAP.items():
        if re.match(variation_regex, syntax_str, flags=re.IGNORECASE):
            return standard_key
    return "default"

# Map standard_syntax_str to set of generic_search_field_set
SYNTAX_GENERIC_MAP = {
    "TIAB=": {"TI=", "AB="},
    "TI=": {"TI="},
    "AB=": {"AB="},
    "TP=": {"TP="},
    "ATP=": {"TP="},
    "WOSTP=": {"TP="},
}

def syntax_str_to_generic_search_field_set(syntax_str: str) -> set:
    standard_syntax_str = map_to_standard(syntax_str)
    generic_search_field_set = SYNTAX_GENERIC_MAP[standard_syntax_str]
    return generic_search_field_set

def generic_search_field_set_to_syntax_set(generic_search_field_set: set) -> set:
    syntax_set = {}
    for key, value in SYNTAX_GENERIC_MAP.items():
        if generic_search_field_set == value:
            syntax_set.add(key)
            # will add TIAB for {TI, AB} but not TI or AB
            # will add TP, ATP, and WOSTP for {TP}
    if not syntax_set:
        raise Exception

    return syntax_set


# search_field string in syntax_1
sf_1 = "TI"
# mapped to a set of generic search fields
sf = {"TI"}
# mapped to a set of strings in syntax_2
sf_2 = {"[ti]"}

# search_field string in syntax_1
sf_1 = "TIAB"
# mapped to a set of generic search fields
sf = {"TI", "AB"}
# mapped to a set of strings in syntax_2
sf_2 = {"TI=", "AB="}

# search_field string in syntax_1
sf_1 = "TIAB"
# mapped to a set of generic search fields
sf = {"TI", "AB"}
# mapped to a set of strings in syntax_2
sf_2 = {"[tiab]"}

# search_field string in syntax_1
sf_1 = "TP"
# mapped to a set of generic search fields
sf = {"TP"}
# mapped to a set of strings in syntax_2
sf_2 = {"[tp]", "[atp]", "[wostp]"}



# linters: operate on syntax-specific fields

# parser: if len(sf_1) > 1:
# create OR query with children for each element in search_field

# TODO : example for creating OR queries (or combining them)