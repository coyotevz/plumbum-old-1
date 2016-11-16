# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'Plumbum',
    version = '0.1.dev1',
    author = 'Augusto Roccasalva',
    author_email = 'augustoroccasalva@gmail.com',
    description = 'Extensible ERP Software',
    long_description = long_description,
    platforms = 'any',
    license = 'MIT',

    packages = find_packages(exclude=['tests']),

    install_requires = [
        'SQLAlchemy',
        'psycopg2',
    ],

    extras_require = {
        'test': ['pytest'],
    },

    entry_points = """\
    [console_scripts]
    plumbum-admin = plumbum.admin.console:main

    [plumbum.plugins]
    plumbum.about = plumbum.about
    plumbum.admin.console = plumbum.admin.console
    plumbum.web.xmlrpc = plumbum.web.xmlrpc
    """
)
