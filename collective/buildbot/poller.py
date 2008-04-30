import os
import sys
import time
import urlparse
import os.path
import datetime
from glob import glob
from os.path import join

from buildbot.changes import svnpoller
from twisted.python import log

from collective.buildbot.utils import split_option

def split_file(path):
    parts = path.split('/')
    if len(parts) < 2:
        return None
    project, branch = parts[0], parts[1]
    return ('%s/%s' % (project, branch), '/'.join(parts[2:]))

class Poller(object):
    """A poller
    """

    def __init__(self, **options):
        self.name = options.get('name')
        self.vcs = options.pop('vcs')
        self.options = options

    def __call__(self, c):
        if self.vcs == 'svn':
            self.setSVNPoller(c)

    def setSVNPoller(self, c):
        """Configure the poller for the project."""
        log.msg('Adding poller to project %s' % self.name)
        svnurl = self.options.get('base_url')
        options = dict(
                pollinterval=int(self.options.get('poll_interval', 600)),
                svnuser=self.options.get('user', None),
                svnpasswd=self.options.get('password', None),
                svnbin=self.options.get('svn_binary', 'svn'),
                split_file=split_file)

        c['change_source'].append(svnpoller.SVNPoller(svnurl, **options))

