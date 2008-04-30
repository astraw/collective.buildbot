import os
import sys
import time
import urlparse
import random
import datetime
from glob import glob
from os.path import join

from buildbot.scheduler import Scheduler
from buildbot.scheduler import Periodic
from buildbot.scheduler import Nightly
from buildbot.process import factory
from buildbot import steps
from buildbot.status import html
from buildbot.status import mail
from buildbot.changes.pb import PBChangeSource
from buildbot.changes import svnpoller
from twisted.python import log

from collective.buildbot.utils import split_option

s = factory.s

def split_file(path):
    parts = path.split('/')
    if len(parts) < 2:
        return None
    project, branch = parts[0], parts[1]
    return ('%s/%s' % (project, branch), '/'.join(parts[2:]))

class Project(object):
    """A builbot project::

        >>> from collective.buildbot.project import Project

    We need to test args::

        >>> project = Project(base_url='https://ingeniweb.svn.sourceforge.net/svnroot/ingeniweb/collective.buildbot',
        ...                   email_notification_sender='gael@ingeniweb.com',
        ...                   email_notification_recipients='gael@ingeniweb.com')

        >>> print project.baseURL
        https://ingeniweb.svn.sourceforge.net

        >>> print project.repository
        /svnroot/ingeniweb/collective.buildbot

        >>> print project.email_notification_sender
        gael@ingeniweb.com
        >>> print project.email_notification_recipients
        ['gael@ingeniweb.com']

    We can have multiple recipients::

        >>> project = Project(base_url='https://ingeniweb.svn.sourceforge.net/svnroot/ingeniweb/collective.buildbot',
        ...                   email_notification_sender='gael@ingeniweb.com',
        ...                   email_notification_recipients='gael@ingeniweb.com buildout@ingeniweb.com')
        >>> print project.email_notification_recipients
        ['gael@ingeniweb.com', 'buildout@ingeniweb.com']

        >>> project = Project(base_url='https://ingeniweb.svn.sourceforge.net/svnroot/ingeniweb/collective.buildbot',
        ...                   email_notification_sender='gael@ingeniweb.com',
        ...                   email_notification_recipients='''gael@ingeniweb.com
        ...                                                 buildout@ingeniweb.com''')
        >>> print project.email_notification_recipients
        ['gael@ingeniweb.com', 'buildout@ingeniweb.com']
    """

    def __init__(self, **options):
        self.name = options.get('name')

        self.mail_host = options.get('mail_host', 'localhost')
        self.email_notification_sender = options.get('email_notification_sender','').strip()
        self.email_notification_recipients = split_option(options,
                                                          'email_notification_recipients')

        self.slave_names =  split_option(options, 'slave_names')
        self.vcs = options.get('vcs', 'svn')

        self.build_sequence = split_option(options, 'build_sequence')
        if not self.build_sequence:
            self.build_sequence = [join(self.executable(), 'bootstrap.py'),
                                   join('bin', 'buildout')]

        self.test_sequence = split_option(options, 'test_sequence')
        if not self.test_sequence:
            self.test_sequence = [join('bin', 'test')]

        base_url = options.get('base_url')
        repository = options.get('repository', '')
        if repository:
            self.baseURL = base_url
            self.repository = repository
        else:
            scheme, host, self.repository = urlparse.urlparse(base_url)[:3]
            if scheme not in ('file', 'svn', 'http', 'https'):
                raise ValueError('Invalid url scheme %s: %s' % (scheme, base_url))
            self.baseURL = base_url.replace(self.repository, '')
        self.branch = options.get('branch', '')

        self.options = options

    def executable(self):
        """returns python bin"""
        return '..%(sep)s..%(sep)sbin%(sep)spython' % dict(sep=os.sep)

    def checkBot(self, c):
        slave_names = [b.slavename for b in c['slaves']]
        for name in self.slave_names:
            if name in slave_names:
                return
        raise RuntimeError('No valid bot name in %r' % self.slave_names)

    def setStatus(self, c):
        if not self.email_notification_sender or not self.email_notification_recipients:
            log.msg('Skiping MailNotifier for project %s: from: %s, to: %s' % (
                      self.name, self.email_notification_sender, self.email_notification_recipients))
        else:
            c['status'].append(mail.MailNotifier(builders=self.builders(),
                           fromaddr=self.email_notification_sender,
                           extraRecipients=self.email_notification_recipients,
                           addLogs=True,
                           relayhost=self.mail_host,
                           mode='failing',
                           sendToInterestedUsers=True))

    def __call__(self, c):
        log.msg('Trying to add %s project' % self.name)
        try:
            self.checkBot(c)
            self.setScheduler(c)
            self.setBuilder(c)
            self.setStatus(c)
        except Exception, e:
            log.msg('Error while adding the %s project: %r %s' % (self.name, e, e))
            raise

        log.msg('Project %s added' % self.name)

    def builder(self, name):
        return '%s %s' % (self.name, name)

    def builders(self):
        return [self.builder(s) for s in self.slave_names]

    def setScheduler(self, c):
        schedulers = []

        scheduler = self.options.get('scheduler', None)
        if scheduler:
            schedulers.append(Scheduler(name=self.name,
                                        branch=self.branch,
                                        treeStableTimer=2*60,
                                        builderNames=self.builders()))

        hours = self.options.get('hours', None)
        if hours:
            minute = random.randint(1, 59)
            if '*' in hours:
                values = '*'
                name = 'Nightly scheduler for %s at *:%s' % (self.name, minute)
            else:
                values = [int(v) for v in hours.split(' ') if v]
                name = 'Nightly scheduler for %s at %s' % (self.name,
                              ' '.join(['%s:%s' % (v, minute) for v in values]))
            schedulers.append(Nightly(name,
                                      self.builders(),
                                      hour=values,
                                      minute=minute))

        log.msg('Adding schedulers for %s: %s' % (self.name, schedulers))

        c['schedulers'].extend(schedulers)

    def setBuilder(self, c):
        executable = self.executable()

        if self.vcs == 'svn':
            svnserver = self.baseURL + self.repository

            update_sequence = [s(steps.source.SVN, mode="update",
                                 baseURL=svnserver, defaultBranch=self.branch)]
        elif self.vcs in  ('hg', 'bzr'):
            if self.vcs == 'hg':
                klass = steps.source.Mercurial
            else:
                klass = steps.source.Bzr

            update_sequence = [s(klass, mode="update", repourl=self.repository)]
        else:
            raise NotImplementedError('%s not supported yet' % self.vcs)

        def _cmd(cmd):
            cmd = [el.strip() for el in cmd.split()]
            if cmd[0].startswith('python'):
                cmd[0] = self.executable()
            return cmd

        build_sequence = [s(steps.shell.ShellCommand, command=_cmd(cmd))
                          for cmd in self.build_sequence
                          if cmd.strip() != '']

        test_sequence = [s(steps.shell.Test, command=_cmd(cmd))
                         for cmd in self.test_sequence
                         if cmd.strip() != '']


        sequence = update_sequence + build_sequence + test_sequence

        for slave_name in self.slave_names:
            log.msg('Adding slave %s to %s project' % (slave_name, self.name))
            name = '%s_%s' % (self.name, slave_name)
            builder = {'name': self.builder(slave_name),
                       'slavename': slave_name,
                       'builddir': name,
                       'factory': factory.BuildFactory(sequence)
                      }

            c['builders'].append(builder)

