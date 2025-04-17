#!/usr/bin/env python3
"""Constants for Web-of-Science."""
# pylint: disable=too-few-public-methods


class WOSSearchFieldList:
    """List of search fields"""

    # Define lists for all search fields
    abstract_list = [
        "AB=",
        "Abstract",
        "ab=",
        "abstract=",
        "ab",
        "abstract",
        "AB",
        "ABSTRACT",
    ]
    language_list = [
        "LA=",
        "Languages",
        "la=",
        "language=",
        "la",
        "language",
        "LA",
        "LANGUAGE",
    ]
    address_list = [
        "AD=",
        "Address",
        "ad=",
        "address=",
        "ad",
        "address",
        "AD",
        "ADDRESS",
    ]
    all_fields_list = [
        "ALL=",
        "All Fields",
        "all=",
        "all fields=",
        "all",
        "all fields",
        "ALL",
        "ALL FIELDS",
    ]
    author_identifiers_list = [
        "AI=",
        "Author Identifiers",
        "ai=",
        "author identifiers=",
        "ai",
        "author identifiers",
        "AI",
        "AUTHOR IDENTIFIERS",
    ]
    author_keywords_list = [
        "AK=",
        "Author Keywords",
        "ak=",
        "author keywords=",
        "ak",
        "author keywords",
        "AK",
        "AUTHOR KEYWORDS",
    ]
    author_list = ["AU=", "Author", "au=", "author=", "au", "author", "AU", "AUTHOR"]
    conference_list = [
        "CF=",
        "Conference",
        "cf=",
        "conference=",
        "cf",
        "conference",
        "CF",
        "CONFERENCE",
    ]
    city_list = ["CI=", "City", "ci=", "city=", "ci", "city", "CI", "CITY"]
    country_region_list = [
        "CU=",
        "Country/Region",
        "cu=",
        "country/region=",
        "cu",
        "country/region",
        "CU",
        "COUNTRY/REGION",
    ]
    doi_list = ["DO=", "DOI", "do=", "doi=", "do", "doi", "DO", "DOI"]
    editor_list = ["ED=", "Editor", "ed=", "editor=", "ed", "editor", "ED", "EDITOR"]
    grant_number_list = [
        "FG=",
        "Grant Number",
        "fg=",
        "grant number=",
        "fg",
        "grant number",
        "FG",
        "GRANT NUMBER",
    ]
    funding_agency_list = [
        "FO=",
        "Funding Agency",
        "fo=",
        "funding agency=",
        "fo",
        "funding agency",
        "FO",
        "FUNDING AGENCY",
    ]
    funding_text_list = [
        "FT=",
        "Funding Text",
        "ft=",
        "funding text=",
        "ft",
        "funding text",
        "FT",
        "FUNDING TEXT",
    ]
    group_author_list = [
        "GP=",
        "Group Author",
        "gp=",
        "group author=",
        "gp",
        "group author",
        "GP",
        "GROUP AUTHOR",
    ]
    issn_isbn_list = [
        "IS=",
        "ISSN/ISBN",
        "is=",
        "issn/isbn=",
        "is",
        "issn/isbn",
        "IS",
        "ISSN/ISBN",
    ]
    keywords_plus_list = [
        "KP=",
        "Keywords Plus®",
        "kp=",
        "keywords plus=",
        "kp",
        "keywords plus",
        "KP",
        "KEYWORDS PLUS",
    ]
    organization_enhanced_list = [
        "OG=",
        "Organization - Enhanced",
        "og=",
        "organization - enhanced=",
        "og",
        "organization - enhanced",
        "OG",
        "ORGANIZATION - ENHANCED",
    ]
    organization_list = [
        "OO=",
        "Organization",
        "oo=",
        "organization=",
        "oo",
        "organization",
        "OO",
        "ORGANIZATION",
    ]
    pubmed_id_list = [
        "PMID=",
        "PubMed ID",
        "pmid=",
        "pubmed id=",
        "pmid",
        "pubmed id",
        "PMID",
        "PUBMED ID",
    ]
    province_state_list = [
        "PS=",
        "Province/State",
        "ps=",
        "province/state=",
        "ps",
        "province/state",
        "PS",
        "PROVINCE/STATE",
    ]
    year_published_list = [
        "PY=",
        "Year Published",
        "py=",
        "year published=",
        "py",
        "year published",
        "PY",
        "YEAR PUBLISHED",
        "Publication Year",
        "publication year",
        "PUBLICATION YEAR",
        "PUBLICATION YEAR",
    ]
    street_address_list = [
        "SA=",
        "Street Address",
        "sa=",
        "street address=",
        "sa",
        "street address",
        "SA",
        "STREET ADDRESS",
    ]
    suborganization_list = [
        "SG=",
        "Suborganization",
        "sg=",
        "suborganization=",
        "sg",
        "suborganization",
        "SG",
        "SUBORGANIZATION",
    ]
    publication_name_list = [
        "SO=",
        "Publication Name",
        "so=",
        "publication name=",
        "so",
        "publication name",
        "SO",
        "PUBLICATION NAME",
    ]
    research_area_list = [
        "SU=",
        "Research Area",
        "su=",
        "research area=",
        "su",
        "research area",
        "SU",
        "RESEARCH AREA",
    ]
    title_list = ["TI=", "Title", "ti=", "title=", "ti", "title", "TI", "TITLE"]
    topic_list = [
        "TS=",
        "Topic",
        "ts=",
        "topic=",
        "ts",
        "topic",
        "TS",
        "TOPIC",
        "Topic Search",
        "Topic TS",
    ]
    accession_number_list = [
        "UT=",
        "Accession Number",
        "ut=",
        "accession number=",
        "ut",
        "accession number",
        "UT",
        "ACCESSION NUMBER",
    ]
    web_of_science_category_list = [
        "WC=",
        "Web of Science Category",
        "wc=",
        "web of science category=",
        "wc",
        "web of science category",
        "WC",
        "WEB OF SCIENCE CATEGORY",
    ]
    zip_postal_code_list = [
        "ZP=",
        "Zip/Postal Code",
        "zp=",
        "zip/postal code=",
        "zp",
        "zip/postal code",
        "ZP",
        "ZIP/POSTAL CODE",
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
        "ZP=": zip_postal_code_list,
    }
