"""Sphinx configuration file for the News Application documentation."""

import os
import sys
import django

sys.path.insert(0, os.path.abspath('..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'news_project.settings'
django.setup()

project = 'News Application'
copyright = '2026, Arian Malayery'
author = 'Arian Malayery'
release = '1.0'

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']
