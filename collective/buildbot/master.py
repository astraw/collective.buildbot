# -*- coding: utf-8 -*-
import os.path
from buildbot.process import factory
from buildbot.changes.pb import PBChangeSource
from buildbot.buildslave import BuildSlave
from buildbot.status import words

from collective.buildbot.overrides import WebStatus
from collective.buildbot.project import Project
from collective.buildbot.poller import Poller
from collective.buildbot.utils import Registry
from ConfigParser import ConfigParser

config = ConfigParser()
config.read([os.environ.get('BUILDBOT_CONFIG',
                            os.path.expanduser('~/buildbot.cfg'))])

if config.has_option('buildbot', 'port'):
    port = config.get('buildbot', 'port') #9989
else:
    port = '9000'

if config.has_option('buildbot', 'wport'):
    wport = config.get('buildbot', 'wport')
else:
    wport = 8999


s = factory.s
# This is the dictionary that the buildmaster pays attention to. We also use
# a shorter alias to save typing.
c = BuildmasterConfig = {}
c['change_source'] = [PBChangeSource()]
# The schedulers and builders are set as part of the project config
c['schedulers'] = []
c['builders'] = []
c['status'] = []

# slave configurations
if config.has_option('buildbot', 'max-builds'):
    max_builds = config.get('buildbot', 'max-builds')
else:
    max_builds = None
if config.has_option('buildbot', 'notify-on-missing'):
    notify_on_missing = [config.get('buildbot', 'notify-on-missing')]
else:
    notify_on_missing = []

c['slaves'] = [BuildSlave(name, password, max_builds=max_builds,
                          notify_on_missing=[],
                          missing_timeout=3600) for name, password in config.items('slaves')]

for name, klass in (('project', Project), ('poller', Poller)):
    registry = Registry()
    dirname = config.get('buildbot', '%ss-directory' % name)
    if os.path.isdir(dirname):
        for filename in os.listdir(dirname):
            if filename.endswith('.cfg'):
                filename = os.path.join(dirname, filename)
                pconf = ConfigParser()
                pconf.read(filename)

                kwargs = dict([(key.replace('-', '_'), value)
                                    for key, value
                                    in pconf.items(name)])
                instance = klass(**kwargs)
                registry.add(instance.name, instance)
    registry.everyone(c, registry)

projects_dir = config.get('buildbot', 'projects-directory')
files = []
for filename in os.listdir(projects_dir):
    if filename.endswith('.cfg'):
        files.append(os.path.join(projects_dir, filename))


######################################################
# Status
allowForce = False
if config.has_option('buildbot', 'allow-force'):
    allowForce = config.get('buildbot', 'allow-force') == 'true'

c['status'].append(WebStatus(http_port=wport, allowForce=allowForce))

#IRC bot if one need it
irc_host = irc_channels = irc_nickname = irc_password = '' 
if config.has_option('buildbot', 'irc-host') and \
   config.has_option('buildbot', 'irc-channels'):
    
    irc_host = config.get('buildbot', 'irc-host')
    irc_channels = config.get('buildbot', 'irc-channels').split()

    if config.has_option('buildbot', 'irc-nickname'):
        irc_nickname = config.get('buildbot', 'irc-nickname')
    else:    
        irc_nickname = 'buildbot'
    if config.has_option('buildbot', 'irc-password'):
        irc_password = config.get('buildbot', 'irc-password')

    irc = words.IRC(irc_host, irc_nickname, irc_channels, password=irc_password)
    c['status'].append(irc)

######################################################
c['slavePortnum'] = port
c['projectName'] = config.get('buildbot', 'project-name')
c['projectURL'] = config.get('buildbot', 'project-url')
c['buildbotURL'] = config.get('buildbot','url')

