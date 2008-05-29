from buildbot.changes import svnpoller
from twisted.python import log
import re

_default_spliter = re.compile(r'(?P<project>\S+\/trunk|\S+\/branches\/[^\/]+)/(?P<relative>.*)')

def split_file(path, splitter=_default_spliter):
    """a splitter based on 'trunk' position::

        >>> print split_file('collective.buildbot/trunk/setup.py')
        ('collective.buildbot/trunk', 'setup.py')

        >>> print split_file('collective.buildbot/branches/super_cool_branch/tests/test.py')
        ('collective.buildbot/branches/super_cool_branch', 'tests/test.py')
    """
    parts = splitter.match(path)
    if parts is not None:
        return (parts.group('project'), parts.group('relative'))

    return None

class Poller(object):
    """A poller
    """

    def __init__(self, **options):
        self.name = options.get('name')
        self.vcs = options.pop('vcs')
        self.options = options

    def __call__(self, c, registry):
        if self.vcs == 'svn':
            self.setSVNPoller(c)

    def setSVNPoller(self, c):
        """Configure the poller for the project."""
        log.msg('Adding poller to project %s' % self.name)
        svnurl = self.options.get('repository')

        if 'splitter' in self.options:
            splitter = re.compile(self.options.pop('splitter'))
        else:
            splitter = _default_spliter

        options = dict(
            pollinterval=int(self.options.get('poll_interval', 600)),
            svnuser=self.options.get('user', None),
            svnpasswd=self.options.get('password', None),
            svnbin=self.options.get('svn_binary', 'svn'),
            split_file=lambda path: split_file(path, splitter))

        c['change_source'].append(svnpoller.SVNPoller(svnurl, **options))

