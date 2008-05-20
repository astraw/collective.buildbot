# -*- coding: utf-8 -*-
from buildbot.scheduler import Scheduler

class RepositoryScheduler(Scheduler):
    """Extend Scheduler to allow multiple projects"""

    def __init__(self, name, branch, treeStableTimer, builderNames,
                 repository, fileIsImportant=None):
        """Override Scheduler.__init__
        Add a new parameter : repository
        """
        Scheduler.__init__(self, name, branch, treeStableTimer,
                           builderNames, fileIsImportant)
        self.repository = repository

    def addChange(self, change):
        """Call Scheduler.addChange only if the repository is modified"""
        change.branch = self.branch
        Scheduler.addChange(self, change)

