# -*- coding: utf-8 -*-
"""
This module contains the tool of collective.recipe.buildbot
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.getcwd(), *rnames)).read()

version = '0.2.0'

long_description = (
    read('README.txt')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
    read('collective', 'buildbot', 'README.txt')
    + '\n' +
    read('collective', 'buildbot', 'docs', 'master.txt')
    + '\n' +
    read('collective', 'buildbot', 'docs', 'slave.txt')
    + '\n' +
    read('collective', 'buildbot', 'docs', 'project.txt')
    + '\n' +
    read('collective', 'buildbot', 'docs', 'poller.txt')
    + '\n' +
    read('collective', 'buildbot', 'docs', 'fullexample.txt')
    + '\n' +
    'Contributors\n'
    '************\n'
    + '\n' +
    read('CONTRIBUTORS.txt')
    + '\n' +
    'Download\n'
    '********\n'
    )
entry_points = {"zc.buildout": [
                    "master = collective.buildbot.master_recipe:Recipe",
                    "slave = collective.buildbot.slave_recipe:Recipe",
                    "project = collective.buildbot.project_recipe:Project",
                    "projects = collective.buildbot.project_recipe:Projects",
                    "poller = collective.buildbot.poller_recipe:Poller",
                    "pollers = collective.buildbot.poller_recipe:Pollers",
                    ],
                }

tests_require=['zope.testing', 'zc.buildout']

setup(name='collective.buildbot',
      version=version,
      description="A set of zc.buildout recipes and package to easy install buildbot",
      long_description=long_description,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Zope Public License',
        ],
      keywords='buildout buildbot',
      author='Gael Pasgrimaud',
      author_email='gael.pasgrimaud@ingeniweb.com',
      url='',
      license='ZPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'zc.buildout',
                        'zc.recipe.egg',
                        'virtualenv',
                        'zope.interface',
                        'Twisted',
                        'buildbot',
                        ],
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      test_suite = 'collective.buildbot.tests.test_docs.test_suite',
      entry_points=entry_points,
      )
