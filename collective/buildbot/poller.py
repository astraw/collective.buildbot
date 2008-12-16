from buildbot.changes import svnpoller
from twisted.python import log
import re

_default_splitter = '(?P<project>\S+\/trunk|\S+\/branches\/[^\/]+)/(?P<relative>.*)'

def split_file(path, splitter=_default_splitter):
    """A splitter based on 'trunk' position::

        >>> print split_file('collective.buildbot/trunk/setup.py')
        ('collective.buildbot/trunk', 'setup.py')
       
    We also can get a branch name out of the branches subtree::
       
        >>> print split_file('collective.buildbot/branches/super_cool_branch/tests/test.py')
        ('collective.buildbot/branches/super_cool_branch', 'tests/test.py')
       
    Ensure that passing in our default splitter as an argument 
    produces the same results::
       
       >>> s = '(?P<project>\S+\/trunk|\S+\/branches\/[^\/]+)/(?P<relative>.*)'
       >>> print split_file('collective.buildbot/trunk/setup.py', s)
       ('collective.buildbot/trunk', 'setup.py')
       >>> print split_file('collective.buildbot/branches/super_cool_branch/tests/test.py')
       ('collective.buildbot/branches/super_cool_branch', 'tests/test.py')
       
    None is expected by buildbot for split_file function when something resides outside
    of the pollers perview::
    
       >>> print split_file('collective.buildbot/foo/bar.py')
       None
    
    But we can alter our splitter to take account for our project specific tree-structure::
        
        >>> s = '(?P<project>\S+\/trunk|\S+\/foo)/(?P<relative>.*)'
        >>> print split_file('collective.buildbot/foo/bar.py', s)
        ('collective.buildbot/foo', 'bar.py')
    
    The aforementioned might be an example of what a cfg's splitter option provides
    to the poller recipe for some internal svn policy.
    """
    splitter = re.compile(r'%s' % splitter)
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
            splitter = self.options.pop('splitter')
        else:
            splitter = _default_splitter
        
        options = dict(
            pollinterval=int(self.options.get('poll_interval', 600)),
            svnuser=self.options.get('user', None),
            svnpasswd=self.options.get('password', None),
            svnbin=self.options.get('svn_binary', 'svn'),
            split_file=lambda path: split_file(path, splitter))

        c['change_source'].append(svnpoller.SVNPoller(svnurl, **options))

