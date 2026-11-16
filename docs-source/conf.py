"""Sphinx configuration for the SunnyPeak Solutions function guide."""

project = "SunnyPeak Solutions"
extensions = ["myst_parser", "sphinx.ext.githubpages"]
root_doc = "index"
myst_heading_anchors = 3

html_theme = "alabaster"
html_title = project
html_theme_options = {
    "page_width": "1120px",
    "sidebar_width": "230px",
    "fixed_sidebar": True,
}
html_sidebars = {"**": ["about.html", "searchfield.html", "localtoc.html"]}
html_show_sourcelink = False
html_copy_source = False
html_use_index = False
html_static_path = ["_static"]
html_css_files = ["guide.css"]
