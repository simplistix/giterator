# -*- coding: utf-8 -*-
import datetime, os, pkg_resources

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

intersphinx_mapping = {
    'http://docs.python.org': None,
}

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    ]

# General
source_suffix = '.rst'
master_doc = 'index'
project = 'giterator'
first_year = 2020
current_year = datetime.datetime.now().year
copyright = (str(current_year) if current_year==first_year else ('%s-%s'%(first_year,current_year)))+' Chris Withers'
version = release = pkg_resources.get_distribution(project).version
exclude_patterns = [
    '_build'
]
pygments_style = 'sphinx'

# Options for HTML output
html_theme = "furo"
html_title = "giterator"
htmlhelp_basename = project+'doc'

# Options for LaTeX output
latex_documents = [
  ('index',project+'.tex', project+u' Documentation',
   'Chris Withers', 'manual'),
]

