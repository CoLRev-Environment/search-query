# scripts/generate_errors_index.py
from pathlib import Path

from search_query.constants import QueryErrorCode

OUTPUT_FILE = Path("docs/source/lint/errors_index.rst")


# OUTPUT_FILE.write_text(".. _query-error-messages:\n\n")
OUTPUT_FILE.write_text("")
with OUTPUT_FILE.open("a", encoding="utf-8") as f:
    # f.write("Lint\n")
    # f.write("====================\n\n")
    # f.write("Overview of query error messages grouped by type.\n\n")

    for group_title, filter_fn in [
        ("Fatal Errors", lambda e: e.is_fatal()),
        ("Errors", lambda e: e.is_error()),
        ("Warnings", lambda e: e.is_warning()),
    ]:
        f.write(f"{group_title}\n{'-' * len(group_title)}\n\n")
        f.write(".. toctree::\n   :maxdepth: 1\n\n")

        for error in filter(filter_fn, QueryErrorCode):
            f.write(f"   {error.code}\n")
            f.write("\n")

OUTPUT_DIR = Path("docs/source/lint")
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
        f"**Scope**: {', '.join(str(e) for e in error.scope)}",
        "",
        error.docs.strip()
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
