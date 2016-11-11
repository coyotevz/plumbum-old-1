# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Plumbum',
    version='0.0a0',
    description='Extensible ERP Software',
    long_description=long_description,
    entry_points={
        'console_scripts': [
            'init=plumbum.commands:mian',
        ],
    }
)
