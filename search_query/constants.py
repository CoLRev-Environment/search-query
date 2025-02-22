#!/usr/bin/env python
"""Constants for search-query"""
# pylint: disable=too-few-public-methods
# pylint: disable=line-too-long
from enum import Enum

# noqa: E501


class PLATFORM(Enum):
    """Database identifier"""

    WOS = "wos"
    PUBMED = "pubmed"
    EBSCO = "ebsco"
    STRUCTURED = "structured"
    PRE_NOTATION = "pre_notation"


class Operators:
    """Operators"""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    NEAR = "NEAR"


class Fields:
    """Search fields"""

    TITLE = "ti"
    ALL = "all"
    ABSTRACT = "ab"
    TOPIC = "ts"
    LANGUAGE = "la"
    YEAR = "py"
    ADDRESS = "ad"
    AUTHOR_IDENTIFIERS = "ai"
    AUTHOR_KEYWORDS = "ak"
    AUTHOR = "au"
    CONFERENCE = "cf"
    CITY = "ci"
    COUNTRY_REGION = "cu"
    DOI = "do"
    EDITOR = "ed"
    GRANT_NUMBER = "fg"
    FUNDING_AGENCY = "fo"
    FUNDING_TEXT = "ft"
    GROUP_AUTHOR = "gp"
    ISSN_ISBN = "is"
    KEYWORDS_PLUS = "kp"
    ORGANIZATION_ENHANCED = "og"
    ORGANIZATION = "oo"
    PUBMED_ID = "pmid"
    PROVINCE_STATE = "ps"
    STREET_ADDRESS = "sa"
    SUBORGANIZATION = "sg"
    PUBLICATION_NAME = "so"
    RESEARCH_AREA = "su"
    ACCESSION_NUMBER = "ut"
    WEB_OF_SCIENCE_CATEGORY = "wc"
    ZIP_POSTAL_CODE = "zp"

    @classmethod
    def all(cls) -> list:
        """Return all fields as a list."""
        return [
            value
            for key, value in vars(cls).items()
            if not key.startswith("_") and not callable(value) and key not in ["all"]
        ]


# The PLATFORM_FIELD_MAP contains the current mapping of standard Fields to the
# syntax of the databases. If a field is not present in the map, it is assumed
# that the field is not supported by the database.
# If multiple options exist for valid database syntax, only the most common
# option is included in the map. Less common options are replaced in the parser.
# For instance, pubmed recommends [mh]. However, [mesh] is also valid and is replaced
# in the parser.
PLATFORM_FIELD_MAP = {
    # fields from
    # https://webofscience.help.clarivate.com/en-us/Content/wos-core-collection/woscc-search-field-tags.htm
    PLATFORM.WOS: {
        Fields.ALL: "ALL=",
        Fields.ABSTRACT: "AB=",
        Fields.TITLE: "TI=",
        Fields.TOPIC: "TS=",
        Fields.LANGUAGE: "LA=",
        Fields.YEAR: "PY=",
        Fields.ADDRESS: "AD=",
        Fields.AUTHOR_IDENTIFIERS: "AI=",
        Fields.AUTHOR_KEYWORDS: "AK=",
        Fields.AUTHOR: "AU=",
        Fields.CONFERENCE: "CF=",
        Fields.CITY: "CI=",
        Fields.COUNTRY_REGION: "CU=",
        Fields.DOI: "DO=",
        Fields.EDITOR: "ED=",
        Fields.GRANT_NUMBER: "FG=",
        Fields.FUNDING_AGENCY: "FO=",
        Fields.FUNDING_TEXT: "FT=",
        Fields.GROUP_AUTHOR: "GP=",
        Fields.ISSN_ISBN: "IS=",
        Fields.KEYWORDS_PLUS: "KP=",
        Fields.ORGANIZATION_ENHANCED: "OG=",
        Fields.ORGANIZATION: "OO=",
        Fields.PUBMED_ID: "PMID=",
        Fields.PROVINCE_STATE: "PS=",
        Fields.STREET_ADDRESS: "SA=",
        Fields.SUBORGANIZATION: "SG=",
        Fields.PUBLICATION_NAME: "SO=",
        Fields.RESEARCH_AREA: "SU=",
        Fields.ACCESSION_NUMBER: "UT=",
        Fields.WEB_OF_SCIENCE_CATEGORY: "WC=",
        Fields.ZIP_POSTAL_CODE: "ZP=",


    },
    # fields from https://pubmed.ncbi.nlm.nih.gov/help/
    PLATFORM.PUBMED: {
        Fields.ALL: "[all]",
        Fields.TITLE: "[ti]",
        Fields.ABSTRACT: "[ab]",
    },
    # fields from https://connect.ebsco.com/s/article/Searching-with-Field-Codes?language=en_US
    PLATFORM.EBSCO: {
        Fields.TITLE: "TI ",
    },
}

# For convenience, modules can use the following to translate fields to a DB
PLATFORM_FIELD_TRANSLATION_MAP = {
    db: {v: k for k, v in fields.items()} for db, fields in PLATFORM_FIELD_MAP.items()
}

PLATFORM_COMBINED_FIELDS_MAP = {
    PLATFORM.PUBMED: {
        "[tiab]": [Fields.TITLE, Fields.ABSTRACT],
    },
}

class ExitCodes:
    """Exit codes"""

    SUCCESS = 0
    FAIL = 1


class Colors:
    """Colors for CLI printing"""

    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


class LinterMode:
    """Linter mode"""
    STRICT = 'strict'
    NONSTRICT = 'non-strict'

class WOSRegex:
    """Regex for WOS"""
    TERM_REGEX = r'\*?[\w-]+(?:[\*\$\?][\w-]*)*|"[^"]+"'
    OPERATOR_REGEX = r'\b(AND|and|OR|or|NOT|not|NEAR/\d{1,2}|near/\d{1,2}|NEAR|near)\b'
    SEARCH_FIELD_REGEX = r'\b\w{2}=|\b\w{3}='
    PARENTHESIS_REGEX = r'[\(\)]'
    SEARCH_FIELDS_REGEX = r'\b(?!and\b)[a-zA-Z]+(?:\s(?!and\b)[a-zA-Z]+)*'
    YEAR_REGEX = r"^\d{4}(-\d{4})?$"
    UNSUPPORTED_WILDCARD_REGEX = r"\!+"
    ISSN_REGEX = r"^\d{4}-\d{3}[\dX]$"
    ISBN_REGEX = r"^(?:\d{1,5}-\d{1,7}-\d{1,7}-[\dX]|\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1})$"
    DOI_REGEX = r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$"

class SearchFieldList:
    """List of search fields"""
    # Define lists for all search fields
    abstract_list = ["AB=", "Abstract", "ab=", "abstract=", "ab", "abstract", "AB", "ABSTRACT"]
    language_list = ["LA=", "Languages", "la=", "language=", "la", "language", "LA", "LANGUAGE"]
    address_list = ["AD=", "Address", "ad=", "address=", "ad", "address", "AD", "ADDRESS"]
    all_fields_list = [
        "ALL=", "All Fields", "all=", "all fields=", "all", "all fields", "ALL", "ALL FIELDS"
    ]
    author_identifiers_list = [
        "AI=", "Author Identifiers", "ai=", "author identifiers=",
        "ai", "author identifiers", "AI", "AUTHOR IDENTIFIERS"
    ]
    author_keywords_list = [
        "AK=", "Author Keywords", "ak=", "author keywords=", "ak",
        "author keywords", "AK", "AUTHOR KEYWORDS"
    ]
    author_list = ["AU=", "Author", "au=", "author=", "au", "author", "AU", "AUTHOR"]
    conference_list = [
        "CF=", "Conference", "cf=", "conference=", "cf", "conference", "CF", "CONFERENCE"
    ]
    city_list = ["CI=", "City", "ci=", "city=", "ci", "city", "CI", "CITY"]
    country_region_list = [
        "CU=", "Country/Region", "cu=", "country/region=",
        "cu", "country/region", "CU", "COUNTRY/REGION"
    ]
    doi_list = ["DO=", "DOI", "do=", "doi=", "do", "doi", "DO", "DOI"]
    editor_list = ["ED=", "Editor", "ed=", "editor=", "ed", "editor", "ED", "EDITOR"]
    grant_number_list = [
        "FG=", "Grant Number", "fg=", "grant number=", "fg", "grant number", "FG", "GRANT NUMBER"]
    funding_agency_list = [
        "FO=", "Funding Agency", "fo=", "funding agency=",
        "fo", "funding agency", "FO", "FUNDING AGENCY"
    ]
    funding_text_list = [
        "FT=", "Funding Text", "ft=", "funding text=",
        "ft", "funding text", "FT", "FUNDING TEXT"
    ]
    group_author_list = [
        "GP=", "Group Author", "gp=", "group author=", "gp",
        "group author", "GP", "GROUP AUTHOR"
    ]
    issn_isbn_list = ["IS=", "ISSN/ISBN", "is=", "issn/isbn=", "is", "issn/isbn", "IS", "ISSN/ISBN"]
    keywords_plus_list = [
        "KP=", "Keywords Plus®", "kp=", "keywords plus=",
        "kp", "keywords plus", "KP", "KEYWORDS PLUS"
    ]
    organization_enhanced_list = [
        "OG=", "Organization - Enhanced", "og=", "organization - enhanced=", 
        "og", "organization - enhanced", "OG", "ORGANIZATION - ENHANCED"
    ]
    organization_list = [
        "OO=", "Organization", "oo=", "organization=",
        "oo", "organization", "OO", "ORGANIZATION"
    ]
    pubmed_id_list = [
        "PMID=", "PubMed ID", "pmid=", "pubmed id=", "pmid", "pubmed id", "PMID", "PUBMED ID"
    ]
    province_state_list = [
        "PS=", "Province/State", "ps=", "province/state=",
        "ps", "province/state", "PS", "PROVINCE/STATE"
    ]
    year_published_list = [
        "PY=", "Year Published", "py=", "year published=", "py", "year published",
        "PY", "YEAR PUBLISHED", "Publication Year", "publication year", "PUBLICATION YEAR", "PUBLICATION YEAR"
    ]
    street_address_list = [
        "SA=", "Street Address", "sa=", "street address=", 
        "sa", "street address", "SA", "STREET ADDRESS"
    ]
    suborganization_list = [
        "SG=", "Suborganization", "sg=", "suborganization=",
        "sg", "suborganization", "SG", "SUBORGANIZATION"
    ]
    publication_name_list = [
        "SO=", "Publication Name", "so=", "publication name=",
        "so", "publication name", "SO", "PUBLICATION NAME"
    ]
    research_area_list = [
        "SU=", "Research Area", "su=", "research area=",
        "su", "research area", "SU", "RESEARCH AREA"
    ]
    title_list = ["TI=", "Title", "ti=", "title=", "ti", "title", "TI", "TITLE"]
    topic_list = ["TS=", "Topic", "ts=", "topic=", "ts", "topic", "TS", "TOPIC", "Topic Search", "Topic TS"]
    accession_number_list = [
        "UT=", "Accession Number", "ut=", "accession number=",
        "ut", "accession number", "UT", "ACCESSION NUMBER"
    ]
    web_of_science_category_list = [
        "WC=", "Web of Science Category", "wc=", "web of science category=",
        "wc", "web of science category", "WC", "WEB OF SCIENCE CATEGORY"
    ]
    zip_postal_code_list = [
        "ZP=", "Zip/Postal Code", "zp=", "zip/postal code=",
        "zp", "zip/postal code", "ZP", "ZIP/POSTAL CODE"
    ]

    search_field_dict = {
        "AB=": abstract_list,
        "AD=": address_list,
        "ALL=": all_fields_list,
        "AI=": author_identifiers_list,
        "AK=": author_keywords_list,
        "AU=": author_list,
        "CF=": conference_list,
        "CI=": city_list,
        "CU=": country_region_list,
        "DO=": doi_list,
        "ED=": editor_list,
        "FG=": grant_number_list,
        "FO=": funding_agency_list,
        "FT=": funding_text_list,
        "GP=": group_author_list,
        "IS=": issn_isbn_list,
        "KP=": keywords_plus_list,
        "LA=": language_list,
        "OG=": organization_enhanced_list,
        "OO=": organization_list,
        "PMID=": pubmed_id_list,
        "PS=": province_state_list,
        "PY=": year_published_list,
        "SA=": street_address_list,
        "SG=": suborganization_list,
        "SO=": publication_name_list,
        "SU=": research_area_list,
        "TI=": title_list,
        "TS=": topic_list,
        "UT=": accession_number_list,
        "WC=": web_of_science_category_list,
        "ZP=": zip_postal_code_list
    }
