import os
from os.path import join

from collective.buildbot.scheduler import SVNScheduler
from buildbot.scheduler import Nightly, Periodic, Dependent
from buildbot.process import factory
from buildbot import steps
from buildbot.steps.python import PyFlakes
from buildbot.status import mail
from twisted.python import log

from collective.buildbot.utils import split_option

s = factory.s

class Project(object):
    """A builbot project::

        >>> from collective.buildbot.project import Project

    We need to test args::

        >>> project = Project(repository='https://ingeniweb.svn.sourceforge.net/svnroot/ingeniweb/collective.buildbot/trunk',
        ...                   email_notification_sender='gael@ingeniweb.com',
        ...                   email_notification_recipients='gael@ingeniweb.com')

        >>> print project.repository
        https://ingeniweb.svn.sourceforge.net/svnroot/ingeniweb/collective.buildbot/trunk

        >>> print project.email_notification_sender
        gael@ingeniweb.com
        >>> print project.email_notification_recipients
        ['gael@ingeniweb.com']

    We can have multiple recipients::

        >>> project = Project(repository='https://ingeniweb.svn.sourceforge.net/svnroot/ingeniweb/collective.buildbot/trunk',
        ...                   email_notification_sender='gael@ingeniweb.com',
        ...                   email_notification_recipients='gael@ingeniweb.com buildout@ingeniweb.com')
        >>> print project.email_notification_recipients
        ['gael@ingeniweb.com', 'buildout@ingeniweb.com']

        >>> project = Project(repository='https://ingeniweb.svn.sourceforge.net/svnroot/ingeniweb/collective.buildbot/trunk',
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
        self.email_notification_recipients = options.get('email_notification_recipients', '').split()
        
        self.slave_names =  options.get('slave_names', '').split()
        self.vcs = options.get('vcs', 'svn')

        self.build_sequence = split_option(options, 'build_sequence')

        self.test_sequence = split_option(options, 'test_sequence')
        if not self.test_sequence:
            self.test_sequence = [join('bin', 'test')]

        self.repository = options.get('repository', '')
        self.branch = options.get('branch', '')
        self.options = options
        self.schedulers = []
        self.username, self.password = self._get_login(self.repository)
 
    def _get_login(self, repository):
        """gets an option in .httpauth"""
        httpauth = join(os.path.expanduser('~'), '.buildout', '.httpauth')
        if not os.path.exists(httpauth):
            return None, None
        for line in open(httpauth):
            realm, url, username, password = (l.strip() for l in line.split(','))
            if repository.startswith(url):
                return username, password
        return None, None
        

    def executable(self):
        """returns python bin"""
        return os.sep.join(['..', '..', 'bin', 'python'])

    def checkBot(self, c):
        slave_names = [b.slavename for b in c['slaves']]
        for name in self.slave_names:
            if name in slave_names:
                return
        raise RuntimeError('No valid bot name in %r' % self.slave_names)

    def setStatus(self, c):
        if not self.email_notification_sender or \
           not self.email_notification_recipients:
            log.msg('Skipping MailNotifier for project %s: from: %s, to: %s' % (
                      self.name, self.email_notification_sender,
                      self.email_notification_recipients))
        else:
            try:
                c['status'].append(mail.MailNotifier(
                        builders=self.builders(),
                        fromaddr=self.email_notification_sender,
                        extraRecipients=self.email_notification_recipients,
                        addLogs=True,
                        relayhost=self.mail_host,
                        mode='failing',
                        sendToInterestedUsers=True))
            except AssertionError:
                log.msg('Error adding MailNotifier for project %s: from: %s, to: %s' % (
                        self.name, self.email_notification_sender,
                        self.email_notification_recipients))

    def __call__(self, c, registry):
        log.msg('Trying to add %s project' % self.name)
        try:
            self.checkBot(c)
            self.setScheduler(c, registry)
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

    def setScheduler(self, c, registry):

        # Always set a scheduler used by pollers
        if self.vcs == 'svn':
            self.schedulers.append(
                    SVNScheduler('Scheduler for %s' % self.name, self.builders(),
                                 repository=self.repository))

        # Set up a simple periodic scheduler
        periodic = self.options.get('periodic_scheduler', None)
        if periodic is not None:
            try:
                period = int(str(periodic).strip())
                if period < 1:
                    raise ValueError

                name = 'Periodic scheduler for %s' % self.name
                self.schedulers.append(Periodic(name, self.builders(), period * 60))
            except (TypeError, ValueError):
                log.msg('Invalid period for periodic scheduler: %s' % period)
                raise

        # Set up a cron-like scheduler
        cron = self.options.get('cron_scheduler', None)
        if cron is not None:
            try:
                minute, hour, dom, month, dow = [v=='*' and v or int(v) for v in cron.split()[:5]]
                name = 'Cron scheduler for %s at %s' % (self.name, cron)
                self.schedulers.append(Nightly(
                        name, self.builders(), minute, hour, dom, month, dow))

            except (IndexError, ValueError, TypeError):
                log.msg('Invalid cron definition for the cron scheduler: %s' % cron)
                raise

        # Set up a dependent scheduler
        dependent = self.options.get('dependent_scheduler')
        if dependent is not None:
            try:
                for parent in registry.runned(dependent, c, registry).schedulers:
                    name = 'Dependent scheduler between scheduler <%s> and project %s' % \
                        (parent.name, self.name)
                    self.schedulers.append(Dependent(name, parent, self.builders()))
            except KeyError:
                log.msg('Invalid project %s selected as dependency' % dependent)
                raise
            except ValueError:
                log.msg('Dependency loop detected')
                raise

        log.msg('Adding schedulers for %s: %s' % (self.name, self.schedulers))

        c['schedulers'].extend(self.schedulers)

    def setBuilder(self, c):
        executable = self.executable()

        if self.vcs == 'svn':
            if self.username is not None and self.password is not None:
                update_sequence = [s(steps.source.SVN, mode="update", svnurl=self.repository,
                                     username=self.username, password=self.password)]
            else:
                update_sequence = [s(steps.source.SVN, mode="update", svnurl=self.repository)]
        elif self.vcs in  ('hg', 'bzr'):
            if self.vcs == 'hg':
                klass = steps.source.Mercurial
            else:
                klass = steps.source.Bzr
            update_sequence = [s(klass, mode="update", repourl=self.repository)]
        elif self.vcs == 'git':
            update_sequence = [s(steps.source.Git, mode='update',
                                 repourl=self.repository, branch=self.branch)]
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

        pyflakes_sequence = []
        if self.options.get('pyflakes', None) is not None:
            pyflakes_cmds = self.options.get('pyflakes').strip().splitlines()
            for pyf in pyflakes_cmds:
                if len(pyf.strip()) > 0:
                    pyflakes_sequence.append(s(PyFlakes, command=pyf.split()))

        sequence = update_sequence + build_sequence + test_sequence + pyflakes_sequence

        for slave_name in self.slave_names:
            log.msg('Adding slave %s to %s project' % (slave_name, self.name))
            name = '%s_%s' % (self.name, slave_name)
            builder = {'name': self.builder(slave_name),
                       'slavename': slave_name,
                       'builddir': name,
                       'factory': factory.BuildFactory(sequence)
                      }

            c['builders'].append(builder)

