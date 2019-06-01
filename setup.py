# -*- coding: utf-8 -*-
"""Installer for the plone.importexport package."""

from setuptools import find_packages
from setuptools import setup


long_description = (
    open('README.rst').read() + '\n' +
    'Contributors\n'
    '============\n\n' +
    open('CONTRIBUTORS.rst').read() + '\n' +
    open('CHANGES.rst').read()
)


setup(
    name='plone.importexport',
    version='0.2.0',
    description="Plone Content import/export",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 5.0.4",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='Python Plone',
    author='Eric BREHAULT',
    author_email='ebrehault@gmail.com',
    url='http://pypi.python.org/pypi/plone.importexport',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['plone'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'plone.api',
        'setuptools',
        'plone.restapi',
        'bs4',
        'unicodecsv'
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'plone.app.contenttypes',
            'plone.app.robotframework[debug]',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
