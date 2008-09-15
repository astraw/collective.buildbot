# -*- coding: utf-8 -*-
# package for paste templates
import string
import random
import socket
import urlparse
from paste.script.templates import Template
from paste.script.templates import var

recipe = 'collective.buildbot'

class Buildbot(Template):
    egg_plugins = [recipe]
    required_templates = []
    summary = 'A template for %s' % recipe
    _template_dir = 'buildbot'
    vars = [
            var(name='port',
                description='the port to use for internal communication',
                default='9050',
                should_echo=True
                ),
            var(name='wport',
                description='the port to use for web interface',
                default='9080',
                should_echo=True
                ),
            var(name='vcs',
                description='the vcs type. hg, bzr and git are supported.',
                default='svn',
                should_echo=True
                ),
            var(name='vcs_url',
                description='the url to checkout from',
                should_echo=True
                ),
           ]

    def pre(self, command, output_dir, vars):
        vars['recipe'] = recipe
        vars['directory'] = '${buildout:directory}'
        vars['password'] = ''.join([random.choice(string.ascii_letters) for i in range(8)])

        vars['hostname'] = socket.gethostname()

        url = vars.get('vcs_url')
        if vars.get('vcs') == 'svn':
            # use the root
            scheme, host = urlparse.urlparse(url)[0:2]
            vars['vcs_root'] = '%s://%s' % (scheme, host)
        else:
            vars['vcs_root'] = url

    def post(self, *args, **kwargs):
        print "Now have a look at master.cfg to finalize your configuration"

