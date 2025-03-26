import os
import sys

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath("../../src"))  # Adjust path to point to your source code

# -- Project information -----------------------------------------------------
project = "agp_api"
author = "brisacoder"
release = "0.0.7"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
]

napoleon_google_docstring = True
autodoc_typehints = "description"
autodoc_class_signature = "separated"

# -- HTML output -------------------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
master_doc = "index"

html_theme_options = {
    'navigation_depth': 2,
}

intersphinx_mapping = {
    'pydantic': ('https://docs.pydantic.dev/latest', None),  
}

autodoc_pydantic_model_show_json = True
autodoc_pydantic_settings_show_json = False