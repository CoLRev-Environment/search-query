#!/usr/bin/env python3
"""Constants for Web-of-Science."""
# pylint: disable=too-few-public-methods


class WOSSearchFieldList:
    """List of search fields"""

    # Define lists for all search fields
    abstract_list = [
        "AB=",
        "ab=",
        "abstract=",
    ]
    language_list = [
        "LA=",
        "la=",
        "language=",
    ]
    address_list = [
        "AD=",
        "ad=",
        "address=",
    ]
    all_fields_list = [
        "ALL=",
        "all=",
        "all fields=",
    ]
    author_identifiers_list = [
        "AI=",
        "ai=",
        "author identifiers=",
    ]
    author_keywords_list = [
        "AK=",
        "ak=",
        "author keywords=",
    ]
    author_list = [
        "AU=",
        "au=",
        "author=",
    ]
    conference_list = [
        "CF=",
        "cf=",
        "conference=",
    ]
    city_list = [
        "CI=",
        "ci=",
        "city=",
    ]
    country_region_list = [
        "CU=",
        "cu=",
        "country/region=",
    ]
    doi_list = [
        "DO=",
        "do=",
        "doi=",
    ]
    editor_list = ["ED=", "ed=", "editor="]
    grant_number_list = [
        "FG=",
        "fg=",
        "grant number=",
    ]
    funding_agency_list = [
        "FO=",
        "fo=",
        "funding agency=",
    ]
    funding_text_list = [
        "FT=",
        "ft=",
        "funding text=",
    ]
    group_author_list = [
        "GP=",
        "gp=",
        "group author=",
    ]
    issn_isbn_list = [
        "IS=",
        "is=",
        "issn/isbn=",
    ]
    keywords_plus_list = [
        "KP=",
        "kp=",
        "keywords plus=",
    ]
    organization_enhanced_list = [
        "OG=",
        "og=",
        "organization - enhanced=",
    ]
    organization_list = [
        "OO=",
        "oo=",
        "organization=",
    ]
    pubmed_id_list = [
        "PMID=",
        "pmid=",
        "pubmed id=",
    ]
    province_state_list = [
        "PS=",
        "ps=",
        "province/state=",
    ]
    year_published_list = [
        "PY=",
        "py=",
        "year published=",
    ]
    street_address_list = [
        "SA=",
        "sa=",
        "street address=",
    ]
    suborganization_list = [
        "SG=",
        "sg=",
        "suborganization=",
    ]
    publication_name_list = [
        "SO=",
        "so=",
        "publication name=",
    ]
    research_area_list = [
        "SU=",
        "su=",
        "research area=",
    ]
    title_list = ["TI=", "ti=", "title="]
    topic_list = [
        "TS=",
        "ts=",
        "topic=",
    ]
    accession_number_list = [
        "UT=",
        "ut=",
        "accession number=",
    ]
    web_of_science_category_list = [
        "WC=",
        "wc=",
        "web of science category=",
    ]
    zip_postal_code_list = [
        "ZP=",
        "zp=",
        "zip/postal code=",
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
