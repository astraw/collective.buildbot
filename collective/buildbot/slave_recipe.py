# -*- coding: utf-8 -*-
"""Recipe devserver"""
import os
import sys
from os.path import join, exists
import zc.buildout
import zc.recipe.egg
from collective.buildbot.recipe import BaseRecipe

class Recipe(BaseRecipe):
    """zc.buildout recipe"""

    def install(self):
        """Installer"""
        # will just create a slave in part, with the right
        # elements, and a start script
        # add the buildbot script
        location = self.location
        if not os.path.exists(location):
            os.mkdir(location)

        self.create_virtualenv(location)
        data = dict([(key.replace('-', '_'), value)
                     for key, value in self.options.items()])
        data['base_dir'] = location
        data['slave_name'] = self.name
        data['umask'] = self.options.get('umask', 'None')

        template = open(join(self.recipe_dir, 'slave.tac_tmpl')).read()
        template = template % data
        filename = join(location, 'buildbot.tac')
        open(filename, 'w').write(template)
        self.log('Generated script %s.' % filename)

        # Create an empty log file if necessary to avoid the error
        # message on first run.
        if not exists(join(location, 'twistd.log')):
            open(join(location, 'twistd.log'), 'w').write('')

        buildbot_cfg = join(location, 'buildbot.tac')

        initialization = initialization_template 
        env_section = self.options.get('environment', '').strip()
        if env_section:
            env = self.buildout[env_section]
            for key, value in env.items():
                initialization += env_template % (key, value)

        options = {'eggs':'collective.buildbot',
                   'entry-points': '%s=collective.buildbot.scripts:main' % self.name,
                   'arguments': 'location=%r, config_file=%r' % (self.location, ''),
                   'initialization': initialization,
                  }

        script = zc.recipe.egg.Egg(self.buildout, self.name, options)

        return list(script.install()) + [filename]

    update = install



initialization_template = """import os
"""

env_template = """os.environ['%s'] = %r
"""
