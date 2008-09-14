Package description
*******************

This package provides a set of zc.buildout_ recipes that make it easy
to configure a buildbot_ setup (build master, build slaves and
projects) and a scripts to run the buildbot master and slaves. The
recipes produce INI-style declarative configuration files based on the
buildout configuration. These configuration files are in turn read by
the buildbot runner script to initialize the buildbot environment.

The available recipes are:

  * ``collective.buildbot:master`` -- Produces a configuration file
    for the build master process.

  * ``collective.buildbot:slave`` -- Produces a configuration file for
    the build slave process.

  * ``collective.buildbot:project`` -- Produces a configuration for a
    project build on a selected slave.

  * ``collective.buildbot:poller`` -- Produces configuration for code
    repository pollers.

It is possible to use all the recipes in a single buildout and have
both the master and slave(s) on the same machine. However, in most
cases you will have one buildout for the build master that uses the
``collective.buildbot:master`` and ``collective.buildbot:project`` to
set up the build processes and then separate buildouts on each of the
slave machines that use the ``collective.buildbot:slave`` recipe.

.. _zc.buildout: http://pypi.python.org/pypi/zc.buildout
.. _buildbot: http://pypi.python.org/pypi/buildbot

Quick start
***********

A paster template is provided with the package to generate a basic
configuration. Just run::

  $ easy_install -U collective.buildbot
  $ paster create -t buildbot my.project
  $ cd my.project

Check the generated configuration in `master.cfg`.

Build the environnement::

  $ python bootstrap.py
  $ ./bin/buildout

Then start deamons::

  $ ./bin/master start
  $ ./bin/yourhostname start

Go to http://localhost:9080 and enjoy your new buildbot


