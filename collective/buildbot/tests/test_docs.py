# -*- coding: utf-8 -*-
"""
Doctest runner for 'collective.buildbot'.
"""
__docformat__ = 'restructuredtext'

import os
from os.path import join
import unittest
import zc.buildout.testing

from zope.testing import doctest, renormalizing

optionflags =  (doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE |
                doctest.REPORT_ONLY_FIRST_FAILURE)

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    # Install any other recipes that should be available in the tests
    zc.buildout.testing.install_develop('zc.recipe.egg', test)
    zc.buildout.testing.install_develop('virtualenv', test)
    zc.buildout.testing.install_develop('zope.interface', test)
    zc.buildout.testing.install_develop('Twisted', test)
    zc.buildout.testing.install_develop('buildbot', test)

    # Install the recipe in develop mode
    zc.buildout.testing.install_develop('collective.buildbot', test)

def test_suite():
    test_files = [
                  'master.txt',
                  'slave.txt',
                  'project.txt',
                  'poller.txt',
                 ]
    suite = unittest.TestSuite([
            doctest.DocFileSuite(
                join('..', 'docs', filename),
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=renormalizing.RENormalizing([
                        # If want to clean up the doctest output you
                        # can register additional regexp normalizers
                        # here. The format is a two-tuple with the RE
                        # as the first item and the replacement as the
                        # second item, e.g.
                        # (re.compile('my-[rR]eg[eE]ps'), 'my-regexps')
                        zc.buildout.testing.normalize_path,
                        ]),
                )
            for filename in test_files])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
