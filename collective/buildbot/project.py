import os
import sys
import time
import urlparse
import os.path
import datetime
from glob import glob
from os.path import join

from buildbot.scheduler import Scheduler
from buildbot.scheduler import Periodic
from buildbot.process import factory
from buildbot import steps
from buildbot.status import html
from buildbot.status import mail
from buildbot.changes.pb import PBChangeSource
from buildbot.changes import svnpoller
from twisted.python import log

from collective.buildbot.scheduler import RepositoryScheduler

s = factory.s

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

    def __init__(self, slave_names='', name='', base_url='', repository='',
                 branch='trunk', test_sequence=None, build_sequence=None,
                 period='24', email_notification_sender='',
                 email_notification_recipients='', mail_host='localhost',
                 vcs='svn', poller=None, poller_url='', **kwargs):
        self.slave_names =  [n.strip() for n in slave_names.split()]
        self.mail_host = mail_host
        self.email_notification_sender = email_notification_sender.strip()
        self.email_notification_recipients = [e.strip() for e in email_notification_recipients.split()]
        self.vcs = vcs
        self.poller = poller
        self.poller_url = poller_url

        if test_sequence is not None:
            self.test_sequence = test_sequence
        else:
            self.test_sequence = join('bin', 'test')

        if build_sequence is not None:
            self.build_sequence = build_sequence
        else:
            self.build_sequence = [join(self.executable(), 'bootstrap.py'),
                                   join('bin', 'buildout')]

        self.name = name
        if repository:
            self.baseURL = base_url
            self.repository = repository
        else:
            scheme, host, self.repository = urlparse.urlparse(base_url)[:3]
            if scheme not in ('file', 'svn', 'http', 'https'):
                raise ValueError('Invalid url scheme %s: %s' % (scheme, base_url))
            self.baseURL = base_url.replace(self.repository, '')
        self.branch = branch
        self.period = int(period)

        self.kwargs = kwargs

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
        c['status'].append(mail.MailNotifier(builders=[self.name],
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
            self.setPoller(c)
        except Exception, e:
            log.msg('Error while adding the %s project: %r %s' % (self.name, e, e))
            raise

        log.msg('Project %s added' % self.name)

    def setPoller(self, c):
        """Configure the poller for the project."""
        if self.poller is None:
            return

        # TODO: Make sure that we don't create duplicate pollers!

        if self.vcs == 'svn':
            log.msg('Adding poller to project %s' % self.name)
            url = self.poller_url or urlparse.urljoin(self.baseURL, self.repository)
            c['change_source'].append(svnpoller.SVNPoller(
                    svnurl=url,
                    pollinterval=int(self.poller.get('poll_interval', 600)),
                    svnuser=self.poller.get('user', None),
                    svnpasswd=self.poller.get('password', None),
                    svnbin=self.poller.get('svn_binary', 'svn'),
                    #split_file=svnpoller.split_file_branches,
                    ))


    def setScheduler(self, c):
        snames = [s.name for s in c['schedulers']]
        slave_names = ['%s_%s' % (self.name, s) for s in self.slave_names]
        periodic = Periodic('Periodic %s' % self.name,
                            slave_names,
                            self.period*60*60)
        scheduler = RepositoryScheduler(
                            name='RepositoryScheduler %s' % self.name,
                            branch=self.branch,
                            treeStableTimer=2*60,
                            builderNames=slave_names,
                            repository=self.repository)
        c['schedulers'].extend([scheduler, periodic])

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
                          for cmd in self.build_sequence.splitlines()
                          if cmd.strip() != '']

        test_sequence = [s(steps.shell.Test, command=_cmd(cmd))
                         for cmd in self.test_sequence.splitlines()
                         if cmd.strip() != '']


        sequence = update_sequence + build_sequence + test_sequence

        for slave_name in self.slave_names:
            log.msg('Adding slave %s to %s project' % (slave_name, self.name))
            name = '%s_%s' % (self.name, slave_name)
            builder = {'name': name,
                       'slavename': slave_name,
                       'builddir': name,
                       'factory': factory.BuildFactory(sequence)
                      }

            c['builders'].append(builder)

