# coding: utf-8
"""
    setup
    ~~~~~

    :copyright: 2014 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from __future__ import unicode_literals
from setuptools import setup
from codecs import open


setup(
    name='zweig',
    version='0.1.0-dev',
    url='https://github.com/DasIch/zweig',
    author='Daniel Neuhäuser',
    author_email='ich@daniel.neuhaeuser.de',
    description='Utilities for dealing with the ast module',
    long_description=open('README.rst', 'r', encoding='utf-8').read(),

    py_modules=['zweig']
)
