import datetime
import sys
from pathlib import Path

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# Resolve the checkout relative to this file.  Sphinx is invoked from both the
# repository root (CI) and ``docs/`` (the Makefile), so a cwd-relative path can
# accidentally import an older, installed version of search-query.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

project = "Search Query"
current_year = datetime.datetime.now().year
copyright = f"{current_year}, Gerit Wagner"
author = "Gerit Wagner"
release = "0.10.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_copybutton",
    "sphinxcontrib.datatemplates",
    "sphinx_design",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
]

templates_path = ["_templates"]
# This fragment is included by lint/index.rst.  Excluding it as a standalone
# source prevents Sphinx from parsing its toctrees a second time.
exclude_patterns = ["lint/errors_index.rst"]


autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
    "css/jquery.dataTables.min.css",
]
html_js_files = ["js/jquery-3.5.1.js", "js/jquery.dataTables.min.js", "js/main.js"]
