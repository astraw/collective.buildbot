# -*- coding: utf-8 -*-
"""Recipe buildmaster"""
import sys
import os
from os.path import join
import shutil
import zc.buildout
import zc.recipe.egg
from collective.buildbot.recipe import BaseRecipe
import virtualenv

class Recipe(BaseRecipe):
    """zc.buildout recipe"""

    def install(self):
        """Installer"""
        files = []
        options = dict([(k, v) for k, v in self.options.items()])
        options.pop('recipe')


        # creates the dir
        if not os.path.exists(self.location):
            os.mkdir(self.location)

        self.create_virtualenv(self.location)

        # adds buildbot.tac
        template = open(join(self.recipe_dir, 'buildbot.tac_tmpl')).read()
        template = template % {'base_dir': self.location}
        buildbot_tac = join(self.location, 'buildbot.tac')
        open(buildbot_tac, 'w').write(str(template))
        self.log('Generated script %r.' % buildbot_tac)
        files.append(buildbot_tac)

        # generates the buildbot.cfg file
        slaves = options.pop('slaves')
        slaves = dict([(slave.split()[0], slave.split()[1])
                  for slave in slaves.split('\n')
                  if slave.strip() != ''])

        parts_directory = join(self.buildout['buildout']['parts-directory'])
        for k in ( 'projects', 'pollers'):
            options.setdefault('%s-directory' % k, join(parts_directory, k))

        for k, v in (('port', '8999'), ('wport', '9000'),
                     ('project-name', 'Buildbot'),
                     ('allow-force', 'false')):
            options.setdefault(k, v)

        for k, v in (('url', 'http://localhost:%s/'),
                     ('project-url', 'http://localhost:%s/')):
            options.setdefault(k, v % options['wport'])

        globs = dict(buildbot=options,
                     slaves=slaves)

        files.append(self.write_config('buildbot', **globs))

        # generate script
        options = {'eggs':'collective.buildbot',
                   'entry-points': '%s=collective.buildbot.scripts:main' % self.name,
                   'arguments': 'location=%r, config_file=%r' % (
                       self.location, join(self.location, 'buildbot.cfg'))
                  }
        script = zc.recipe.egg.Egg(self.buildout, self.name, options)
        files.extend(list(script.install()))

        return files


    update = install
