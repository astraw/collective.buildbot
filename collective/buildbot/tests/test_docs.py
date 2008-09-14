# -*- coding: utf-8 -*-
"""
Doctest runner for 'collective.buildbot'.
"""
__docformat__ = 'restructuredtext'

from os.path import join
import os
import unittest
import zc.buildout.testing

from zope.testing import doctest, renormalizing
import collective.buildbot.poller
import collective.buildbot.project
import collective.buildbot.project_recipe

optionflags =  (doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE |
                doctest.REPORT_ONLY_FIRST_FAILURE)

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    os.makedirs(join(os.path.expanduser('~'), '.buildout'))
    fd = open(join(os.path.expanduser('~'), '.buildout', 'default.cfg'), 'w')
    fd.write('''[buildout]\noffline=true''')
    fd.close()

    # Install any other recipes that should be available in the tests

    zc.buildout.testing.install('Paste', test)
    zc.buildout.testing.install('PasteDeploy', test)
    zc.buildout.testing.install('PasteScript', test)
    zc.buildout.testing.install_develop('zc.recipe.egg', test)
    zc.buildout.testing.install_develop('virtualenv', test)
    zc.buildout.testing.install_develop('zope.interface', test)
    zc.buildout.testing.install_develop('Twisted', test)
    zc.buildout.testing.install_develop('buildbot', test)
    try:
        zc.buildout.testing.install_develop('pyflakes', test)
    except AttributeError:
        pass

    # Install the recipe in develop mode
    zc.buildout.testing.install_develop('collective.buildbot', test)

def test_suite():

    # doc file suite
    test_files = [
                  'master.txt',
                  'slave.txt',
                  'project.txt',
                  'poller.txt',
                  'fullexample.txt',
                  'svnauth.txt'
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

    # doc test suite
    suite.addTest(doctest.DocTestSuite(collective.buildbot.poller))
    suite.addTest(doctest.DocTestSuite(collective.buildbot.project))
    suite.addTest(doctest.DocTestSuite(collective.buildbot.project_recipe))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
