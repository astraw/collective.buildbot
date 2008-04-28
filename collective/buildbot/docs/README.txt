The master recipe
*****************

Supported options
=================

The recipe supports the following options:

port
    The port buildbot listens to. Called by slaves.

wport
    The web port buildbot use to display the fountain.

project-name
    Project name. Displayed in the web pages.

project-url
    Project url, used in the web pages.

url
    buildbot url.

build-slaves
    Lists the slaves, with the name and the password for each.

projects
    Lists the projects the buildbot deal with (one project=one column)
    The values must be a section name in the configuration file.
    Then each of this section must contain:
    
    - slave-name: the slave used
    - base-url: base url for the project (Subversion)
    - repository: path in the repository
    - branch: last part of the url 
    - build-sequence: The sequence of shell
      commands to build the project.
      Defaults to:
      
      - bin/python boostrap.py
      - bin/buildout

    - test-sequence: The sequence of shell
      commands that are run to test the project.
      Defaults to 'bin/test'
    
    The buildbot will use base-url/repository/branch to 
    get the full url to be retrieved for the checkout.

Example usage
=============

We'll start by creating a buildout that uses the recipe::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = buildmaster
    ... 
    ... [buildmaster]
    ... recipe = collective.buildbot:master
    ... port = 8080
    ... wport = 8082
    ... project-name = The project
    ... project-url = http://example.com
    ... url = http://example.com/buildbot
    ... slaves = 
    ...     slave1 password
    ...     slave2 password
    ... projects = 
    ...     one
    ...     two
    ...
    ... [one]
    ... slave-names = slave1
    ... email-notification-sender = foo@bar.com
    ... email-notification-recipient =
    ...     bar@foo.com
    ...     buildbot@foo.com
    ... base-url = http://example.com 
    ... repository = svn/my.package
    ... branch = trunk
    ...
    ... [two]
    ... slave-names = slave2
    ... email-notification-sender = foobar@barfoo.com
    ... email-notification-recipient = barfoo@foobar.com
    ... base-url = http://example.com
    ... repository = svn/buildout
    ... branch = trunk
    ... test-sequence =
    ...     bin/zopeinstance test -s product.one
    ...     bin/zopeinstance test -s product.two
    ... """)

Running the buildout gives us::

    >>> print system(buildout)
    Installing buildmaster.
    ...
    Generated script /sample-buildout/parts/buildmaster/buildbot.tac.
    Generated script /sample-buildout/parts/buildmaster/buildbot.cfg.
    Generated script /sample-buildout/parts/buildmaster/projects/one.cfg.
    Generated script /sample-buildout/parts/buildmaster/projects/two.cfg.
    Generated script /sample-buildout/bin/buildmaster.py.
    <BLANKLINE>

As shown above, the buildout generated the required configuration files.
TODO: Add proper documentation!

Twisted .tac file to launch buildbot::

    >>> cat(join('parts', 'buildmaster', 'buildbot.tac'))
    from twisted.application import service
    from buildbot.master import BuildMaster
    import os
    import sys
    import collective.buildbot
    <BLANKLINE>
    basedir = '/sample-buildout/parts/buildmaster'
    buildbot = os.path.dirname(collective.buildbot.__file__)
    <BLANKLINE>
    configfile = os.path.join(buildbot, 'master.py')
    application = service.Application('buildmaster')
    <BLANKLINE>
    master = BuildMaster(basedir, configfile)
    master.setServiceParent(application)
    <BLANKLINE>

A buildout config file::

    >>> cat(join('parts', 'buildmaster', 'buildbot.cfg'))
    [buildbot]
    port=8080
    wport=8082
    allow-force=false
    project-name=The project
    project-url=http://example.com
    buildbot-url=http://example.com/buildbot
    projects-directory = /sample-buildout/parts/buildmaster/projects 
    <BLANKLINE>
    [slaves]
    slave1=password
    slave2=password
    <BLANKLINE>

A project config::

    >>> cat(join('parts', 'buildmaster', 'projects', 'one.cfg'))
    [one]
    base-url=http://example.com
    branch=trunk
    build-sequence=
    python bootstrap.py    
    bin/buildout
        email-notification-recipient=
        bar@foo.com
        buildbot@foo.com
    email-notification-sender=foo@bar.com
    mail-host=localhost
    name=one
    repository=svn/my.package
    slave-names=slave1
    test-sequence=
    bin/test --exit-with-status
    vcs=svn
    <BLANKLINE>

Another one::

    >>> cat(join('parts', 'buildmaster', 'projects', 'two.cfg'))
    [two]
    base-url=http://example.com
    branch=trunk
    build-sequence=
        python bootstrap.py    
        bin/buildout
    email-notification-recipient=barfoo@foobar.com
    email-notification-sender=foobar@barfoo.com
    mail-host=localhost
    name=two
    repository=svn/buildout
    slave-names=slave2
    test-sequence=
        bin/zopeinstance test -s product.one    
        bin/zopeinstance test -s product.two
    vcs=svn
    <BLANKLINE>

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = buildmaster-poller
    ... 
    ... [buildmaster-poller]
    ... recipe = collective.buildbot:master
    ... port = 8080
    ... wport = 8082
    ... project-name = The project
    ... project-url = http://example.com
    ... url = http://example.com/buildbot
    ... slaves = 
    ...     slave1 password
    ...     slave2 password
    ... projects = 
    ...     one
    ...     two
    ...
    ... [one]
    ... slave-names = slave1
    ... email-notification-sender = foo@bar.com
    ... email-notification-recipient =
    ...     bar@foo.com
    ...     buildbot@foo.com
    ... base-url = http://example.com 
    ... repository = svn/my.package
    ... branch = trunk
    ... poller = svnpoller
    ...
    ... [two]
    ... slave-names = slave2
    ... email-notification-sender = foobar@barfoo.com
    ... email-notification-recipient = barfoo@foobar.com
    ... base-url = http://example.com
    ... repository = svn/buildout
    ... branch = trunk
    ... poller = svnpoller
    ... test-sequence =
    ...     bin/zopeinstance test -s product.one
    ...     bin/zopeinstance test -s product.two
    ... 
    ... [svnpoller]
    ... url = http://example.com/svn/buildout
    ... user = h4x0r
    ... password = passwd
    ... poll-interval = 600
    ... hist-max = 100
    ... svn-binary = svn
    ... multi-branch = false
    ... """)

    >>> print system(buildout)
    Uninstalling buildmaster.
    Installing buildmaster-poller.
    ...
    Generated script /sample-buildout/parts/buildmaster-poller/buildbot.tac.
    Generated script /sample-buildout/parts/buildmaster-poller/buildbot.cfg.
    Generated script /sample-buildout/parts/buildmaster-poller/projects/one.cfg.
    Generated script /sample-buildout/parts/buildmaster-poller/projects/two.cfg.
    Generated script /sample-buildout/bin/buildmaster-poller.py.
    <BLANKLINE>

Poller generation::

    >>> cat(join('parts', 'buildmaster-poller', 'projects', 'one.cfg'))
    [one]
    base-url=http://example.com
    branch=trunk
    build-sequence=
        python bootstrap.py    
        bin/buildout
    email-notification-recipient=
        bar@foo.com
        buildbot@foo.com
    email-notification-sender=foo@bar.com
    mail-host=localhost
    name=one
    repository=svn/my.package
    slave-names=slave1
    test-sequence=
        bin/test --exit-with-status
    vcs=svn
    <BLANKLINE>
    [poller]
    hist-max=100
    multi-branch=false
    password=passwd
    poll-interval=600
    svn-binary=svn
    url=http://example.com/svn/buildout
    user=h4x0r

The slave recipe
****************

Supported options
=================

The recipe supports the following options:

host
    Host of the buildmaster.
    
port
    Port on which the buildmaster listens.

password
    Sets the password for the buildbot.

Example usage
=============

We'll start by creating a buildout that uses the recipe::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = 
    ...	   buildslave
    ... 
    ... [buildslave]
    ... recipe = collective.buildbot:slave
    ... host = localhost
    ... port = 8888
    ... password = password
    ... """)

Running the buildout gives us::

    >>> print system(buildout)
    Uninstalling buildmaster-poller.
    Installing buildslave.
    ...
    Generated script /sample-buildout/parts/buildslave/buildbot.tac.
    Generated script /sample-buildout/bin/buildslave.py.
    <BLANKLINE>

