# -*- coding: utf-8 -*-
"""Recipe devserver"""
import sys
import os
import glob
import shutil
from os.path import join
import zc.buildout
import zc.recipe.egg
from collective.buildbot.recipe import BaseRecipe
import virtualenv

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

        template = open(join(self.recipe_dir, 'slave.tac_tmpl')).read()
        template = template % data
        filename = join(location, 'buildbot.tac')
        open(filename, 'w').write(template)
        self.log('Generated script %s.' % filename)

        buildbot_cfg = join(location, 'buildbot.tac')
        options = {'eggs':'collective.buildbot',
                   'entry-points': '%s=collective.buildbot.scripts:main' % self.name,
                   'arguments': 'location=%r, config_file=%r' % (self.location, '')
                  }
        script = zc.recipe.egg.Egg(self.buildout, self.name, options)

        return list(script.install()) + [filename]

    update = install

