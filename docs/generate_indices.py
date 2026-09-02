import json
import re
import sys
from pathlib import Path

# Always generate from the checkout rather than a possibly stale installed
# distribution, regardless of the directory from which this script is run.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    from importlib.resources import files
except ImportError:  # pragma: no cover - Python 3.8
    from importlib_resources import files

from search_query.constants import QueryErrorCode

# ruff: noqa: E501
# flake8: noqa: E501

OUTPUT_FILE = REPO_ROOT / "docs/source/lint/errors_index.rst"


# OUTPUT_FILE.write_text(".. _query-error-messages:\n\n")
OUTPUT_FILE.write_text("")
with OUTPUT_FILE.open("a", encoding="utf-8") as f:
    # f.write("Lint\n")
    # f.write("====================\n\n")
    # f.write("Overview of query error messages grouped by type.\n\n")

    for group_title, filter_fn in [
        ("Parsing errors", lambda e: e.code.startswith("PARSE_")),
        ("Deprecated syntax", lambda e: e.code.startswith("LINT_")),
        ("Query structure errors", lambda e: e.code.startswith("STRUCT_")),
        ("Term errors", lambda e: e.code.startswith("TERM_")),
        ("Field errors", lambda e: e.code.startswith("FIELD_")),
        ("Database errors: Web of Science", lambda e: e.code.startswith("WOS_")),
        ("Database errors: EBSCOHost", lambda e: e.code.startswith("EBSCO_")),
        ("Database errors: PubMed", lambda e: e.code.startswith("PUBMED_")),
        ("Best practice qualities", lambda e: e.code.startswith("QUALITY_")),
    ]:
        f.write(f"{group_title}\n{'-' * len(group_title)}\n\n")
        f.write(".. toctree::\n   :maxdepth: 1\n\n")

        for error in filter(filter_fn, QueryErrorCode):
            f.write(f"   {error.code}\n")
            f.write("\n")

# Keep generated output stable and leave exactly one newline at EOF.
OUTPUT_FILE.write_text(
    OUTPUT_FILE.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8"
)

OUTPUT_DIR = REPO_ROOT / "docs/source/lint"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_rst_file(error: QueryErrorCode) -> None:
    """Generate a single .rst file for a given QueryErrorCode"""
    filename = OUTPUT_DIR / f"{error.code}.rst"

    header = f"{error.code} — {error.label}"
    underline = "=" * len(header)

    content_lines = [
        f".. _{error.code}:\n",
        header,
        underline,
        "",
        f"**Error Code**: {error.code}",
        "",
        f"**Message**: ``{error.message}``",
        "",
        error.docs.strip().replace("code-block:: texts", "code-block:: text")
        if error.docs.strip()
        else "**Description**: " + error.message,
        "",
        "**Back to**: :ref:`lint`",
        "",
    ]

    filename.write_text("\n".join(content_lines), encoding="utf-8")
    print(f"Generated: {filename}")


for error in QueryErrorCode:
    generate_rst_file(error)


# OUTPUT_FILE = Path("docs/source/parser/parser_index.rst")
# OUTPUT_FILE.write_text(".. _parsers:\n\n")
# with OUTPUT_FILE.open("a", encoding="utf-8") as f:
#     f.write("Parsers\n")
#     f.write("====================\n\n")
#     f.write("Overview of query parsers:\n\n")
#     # f.write(".. toctree::\n   :maxdepth: 1\n\n")

#     for platform in PLATFORM:
#         f.write(f"- {platform.value}\n")
#         # f.write(f" parser/{platform}.rst\n")
#         f.write("\n")


query_dir = files("search_query") / "json_db"
output_dir = REPO_ROOT / "docs/source/query_database"
rst_dir = output_dir / "queries"
rst_dir.mkdir(parents=True, exist_ok=True)

overview = []


def slugify(name: str) -> str:
    return re.sub(r"[^\w\-]+", "-", name.lower()).strip("-")


for file in sorted(
    query_dir.iterdir(), key=lambda path: (path.name.casefold(), path.name)
):
    if file.suffix == ".json":
        with open(file, encoding="utf-8") as f:
            content = json.load(f)

        identifier = file.stem
        platform = content.get("platform", "")
        search_string = content.get("search_string", "")
        title = content.get("title", identifier)
        description = content.get("description", "")
        keywords = content.get("keywords", "")
        filename = file.name
        authors = " and ".join(x["name"] for x in content.get("authors", []))
        license = content.get("license", "")

        slug = slugify(identifier)
        rst_filename = rst_dir / f"{slug}.rst"

        # Write individual .rst file
        with open(rst_filename, "w", encoding="utf-8") as rst:
            rst.write(
                f"""{title}
{'=' * len(title)}

**Identifier**: ``{identifier}``

**Platform**: ``{platform}``

**Keywords**: ``{keywords}``

**Authors**: ``{authors}``

**License**: ``{license}``

**License**: {description}

Load
-----------

.. code-block:: python

    from search_query.database import load_query

    query = load_query("{filename}")

    print(query.to_string())
    # {search_string[:80] + "..."}


Search String
-------------

.. raw:: html

    <pre style="white-space: pre-wrap; word-break: break-word;">
    {search_string}
    </pre>


Suggest to `improve this query <https://github.com/CoLRev-Environment/search-query/blob/main/search_query/json_db/{filename}>`_.
"""
            )

        overview.append(
            {
                "identifier": f"`{identifier} <queries/{slug}.html>`_",
                "platform": platform,
                "search_string_snippet": search_string[:80] + "...",
                "title": title,
                "description": description,
                "keywords": keywords,
            }
        )

# Write overview.json
with open(output_dir / "query_overview.json", "w", encoding="utf-8") as f:
    json.dump(overview, f, indent=2)
