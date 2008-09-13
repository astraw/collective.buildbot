# -*- coding: utf-8 -*-
# package for paste templates
import string
import random
from paste.script.templates import Template
from paste.script.templates import var

recipe = 'collective.buildbot'

class Simple(Template):
    egg_plugins = [recipe]
    summary = 'A simple template for %s' % recipe
    required_templates = []
    _template_dir = 'simple'
    vars = [
            var(name='port',
                description='the port to use for internal communication',
                default='9050',
                should_echo=True
                ),
            var(name='wport',
                description='the port to use for web interface',
                default='980',
                should_echo=True
                ),
            var(name='vcs',
                description='the vcs type',
                default='svn',
                should_echo=True
                ),
            var(name='vcs_url',
                description='the vcs url to checkout from',
                should_echo=True
                ),
           ]

    def pre(self, command, output_dir, vars):
        vars['recipe'] = recipe
        vars['password'] = ''.join([random.choice(string.ascii_letters) for i in range(8)])
        print vars
