# -*- coding: utf-8 -*-
import datetime
import time
import os.path
import os
from buildbot.process import buildstep, factory
from buildbot.status import html
from buildbot.changes.pb import PBChangeSource
from buildbot.buildslave import BuildSlave

from twisted.python import log
from collective.buildbot.project import Project
from ConfigParser import ConfigParser

config = ConfigParser()
config.read([os.environ.get('BUILDBOT_CONFIG', 
                            os.path.expanduser('~/buildbot.cfg'))])

port = config.get('buildbot', 'port') #9989
wport = config.get('buildbot', 'wport') #8010


s = factory.s
# This is the dictionary that the buildmaster pays attention to. We also use
# a shorter alias to save typing.
c = BuildmasterConfig = {}
c['change_source'] = [PBChangeSource()]
# The schedulers and builders are set as part of the project config
c['schedulers'] = []
c['builders'] = []
c['status'] = []


c['slaves'] = [BuildSlave(bot, passwd) for bot, passwd
               in config.items('slaves')]

projects_dir = config.get('buildbot', 'projects-directory')
files = []
for filename in os.listdir(projects_dir):
    if filename.endswith('.cfg'):
        files.append(os.path.join(projects_dir, filename))


for projectcfg in files:
    pconf = ConfigParser()
    pconf.read(projectcfg)

    kwargs = {}
    for section in pconf.sections():
        if section == 'poller':
            kwargs['poller'] = dict([(key.replace('-', '_'), value)
                                     for key, value
                                     in pconf.items(section)])
        else:
            kwargs.update(dict([(key.replace('-', '_'), value)
                                for key, value
                                in pconf.items(section)]))
    kwargs['name'] = section
    Project(**kwargs)(c)


######################################################
# Status
allowForce = False
if config.has_option('buildbot', 'allow-force'):
    allowForce = config.get('buildbot', 'allow-force') == 'true'


c['status'].append(html.WebStatus(http_port=wport, allowForce=allowForce))
######################################################
c['slavePortnum'] = port
c['projectName'] = config.get('buildbot', 'project-name') 
c['projectURL'] = config.get('buildbot', 'project-url')
c['buildbotURL'] = config.get('buildbot','buildbot-url') 

