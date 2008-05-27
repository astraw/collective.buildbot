# -*- coding: utf-8 -*-
from buildbot.scheduler import Scheduler

class SVNScheduler(Scheduler):
    """Extend Scheduler to allow multiple projects"""

    def __init__(self, name, builderNames, repository):
        """Override Scheduler.__init__
        Add a new parameter : repository
        """
        Scheduler.__init__(self, name, None, 120,
                           builderNames, fileIsImportant=None)
        self.repository = repository

    def addChange(self, change):
        """Call Scheduler.addChange only if the branch name (eg. project name
        in your case) is in the repository url"""
        if isinstance(change.branch, basestring):
            if change.branch in self.repository:
                change.branch = None
                Scheduler.addChange(self, change)

