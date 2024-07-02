#!/usr/bin/env python3
"""Script to import searchRxiv data to SearchQuery format."""
import datetime
import json
import os
from pathlib import Path

import inquirer

import search_query.exception as search_query_exception
from search_query.parser import parse
from search_query.search_file import SearchHistoryFile

# pylint: disable=invalid-name

SYNTAX_MAP = {
    "web of science": "wos",
    "wos": "wos",
    # "pubmed": "pubmed",
    # "medline": "pubmed",
    # "pubmed.gov": "pubmed",
    # "nlm": "pubmed",
    # "scopus.com": "scopus",
    # "scopus": "scopus",
    # "embase.com": "embase",
    # "embase": "embase",
    # "ebscohost": "ebscohost",
    # "ebsco": "ebscohost",
    # "ebsco host": "ebscohost",
    # "ebscohost research databases": "ebscohost",
    # "ovid": "ovid",
    # "ovid sp": "ovid",
    # "psycinfo": "psycinfo",
    # "proquest": "proquest",
    # "elsevier": "scopus",
    # "google scholar": "googlescholar",
    # "scholar.google.com": "googlescholar",
    # "wiley": "wiley",
    # "cochrane library": "cochrane",
    # "cochrane": "cochrane",
    # "ieee": "ieee",
    # "scielo": "scielo",
    # "emerald full text": "emerald",
    # "cinahl complete": "cinahl",
    # "clinicaltrials.gov": "clinicaltrials",
    # "springerlink": "springer",
    # "agris": "agris",
    # "solr": "solr",
    # "doaj": "doaj",
    # "eric": "eric",
    # "sciencedirect": "sciencedirect",
    # "vhl": "vhl",
}

DB = {}

parent_directory = "/home/gerit/ownCloud/projects/SearchQuery/wip/"

source_directory = parent_directory + "searchRxiv_scraper/data"
target_directory = parent_directory + "search-query/data"
target_directory_failure = parent_directory + "search-query/data_erroneous"

coder_initials = "GW"

for filename in os.listdir(source_directory):
    if filename.endswith(".json"):
        filepath = os.path.join(source_directory, filename)
        with open(filepath, encoding="utf-8") as file:
            data = json.load(file)

            if "Platform" not in data.get("content", {}) or "Search" not in data.get(
                "content", {}
            ):
                print(f"Error in {filepath}")
                continue

            platform = data["content"]["Platform"].strip().lower()
            if platform not in SYNTAX_MAP:
                # print(f"Platform not available: {platform}")
                continue

            syntax = SYNTAX_MAP[platform]
            # Construct the target directory path based on the syntax
            target_syntax_directory = Path(target_directory) / syntax
            target_syntax_directory_failure = Path(target_directory_failure) / syntax

            # Create the target directory if it doesn't exist
            target_syntax_directory.mkdir(parents=True, exist_ok=True)
            target_syntax_directory_failure.mkdir(parents=True, exist_ok=True)

            # Write the data as JSON to the target file
            target_file_success = target_syntax_directory / filename
            target_file_failure = target_syntax_directory_failure / filename
            if target_file_success.is_file() or target_file_failure.is_file():
                continue
            print("\n\n\n\n\n")
            print(filepath)
            if syntax not in DB:
                DB[syntax] = {"count": 0, "success": 0, "fail": 0}
            DB[syntax]["count"] += 1

            status, comment = "todo", "todo"
            query_string = data["content"]["Search"]
            # print(query_string)
            try:
                ret = parse(query_string, query_type=syntax)
                # Could start with smaller queries:
                # if ret.get_nr_leaves() > 15:
                #     continue
                print(query_string)
                print(ret.to_string("structured"))
                query_pre_notation = ret.to_string("pre_notation")
                print(query_pre_notation)
                DB[syntax]["success"] += 1

            # TODO : temporarily disabled
            except search_query_exception.QuerySyntaxError as exc:
                print(query_string)
                print(exc)
                status = "QuerySyntaxError"
                DB[syntax]["fail"] += 1
            except Exception as exc:
                # print(exc)
                DB[syntax]["fail"] += 1
                raise exc

            print()
            if status == "todo":
                status = inquirer.prompt(
                    [
                        inquirer.List(
                            "status",
                            message="Select status:",
                            choices=["skip", "success", "fail"],
                        )
                    ]
                )["status"]
            elif status == "QuerySyntaxError":
                confirmed = inquirer.prompt(
                    [
                        inquirer.Confirm(
                            "status", message="Confirm status:", default=False
                        )
                    ]
                )["status"]
                if confirmed:
                    comment = "QuerySyntaxError"
                    status = "fail"
                else:
                    status = "skip"

            if status == "skip":
                continue

            if comment == "todo":
                comment = input("Comment")

            search_history = {}
            search_history["record_info"] = {
                "DOI": data["doi"].replace("https://doi.org/", ""),
                "url": data["url"],
            }
            search_history["authors"] = [  # type: ignore
                {"name": author} for author in data["author"].split(" and ")
            ]
            search_history["platform"] = data["content"]["Platform"]
            search_history["database"] = [data["content"]["Database Searched"]]  # type: ignore
            search_history["search_string"] = data["content"]["Search"]
            search_history["date"] = {}
            if "Search Conducted Date" in data["content"]:
                search_history["date"]["search_conducted"] = data["content"][
                    "Search Conducted Date"
                ].replace("-", ".")

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

            # Note : custom extension of SearchHistoryFile
            search_history["parsed"] = {}
            # data["parsed"]["Status"] = status
            search_history["parsed"]["search"] = query_pre_notation
            search_history["parsed"]["coder"] = coder_initials
            search_history["parsed"]["timestamp"] = timestamp
            search_history["parsed"]["comment"] = comment

            # validate
            SearchHistoryFile(**search_history)

            if status == "success":
                with open(target_file_success, "w", encoding="utf-8") as file:
                    json.dump(search_history, file, indent=4)
            elif status == "fail":
                with open(target_file_failure, "w", encoding="utf-8") as file:
                    json.dump(search_history, file, indent=4)

            input("CONTINUE")

print()
sorted_db = sorted(DB.items(), key=lambda x: x[1]["count"], reverse=True)
for platform, data in sorted_db:
    count = data["count"]
    if count < 30:
        continue
    print(f"{platform}: {count}")
    print(f"Syntax: {platform}")
    print(f"Parsed: {data['success']}")
    print(f"Fail: {data['fail']}")
    print()
