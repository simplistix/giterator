from importlib import metadata

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

# General
source_suffix = '.rst'
master_doc = 'index'
project = 'giterator'
copyright = '2020 onwards Chris Withers'
version = release = metadata.version(project)
exclude_patterns = ['_build']
pygments_style = 'sphinx'
autodoc_member_order = 'bysource'

# Options for HTML output
html_theme = 'furo'
html_title = 'giterator'
htmlhelp_basename = project + 'doc'
