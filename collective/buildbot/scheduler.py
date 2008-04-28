# -*- coding: utf-8 -*-
import datetime, time, os.path
from buildbot.scheduler import Scheduler, Nightly
from buildbot.process import buildstep, factory
from buildbot.status import html
from buildbot.status import mail
from buildbot.changes.pb import PBChangeSource
from twisted.python import log


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

