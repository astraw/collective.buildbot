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

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        eggs = zc.recipe.egg.Eggs(buildout, 'eggs', dict(eggs='collective.buildbot'))
        options['bin-directory'] = buildout['buildout']['bin-directory']
        options['scripts'] = '' # suppress script generation.
        parts_dir = buildout['buildout']['parts-directory']
        options['location'] = join(parts_dir, self.name)
        _, self.ws = eggs.working_set()

    def install(self):
        """Installer"""
        # will just create a slave in part, with the right
        # elements, and a start script
        # add the buildbot script
        location = self.options['location']
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

        # add the buildbot script
        bin_dir = self.options['bin-directory']
        paths = ["'%s'" % d.location for d in self.ws]
        template = open(join(self.recipe_dir, 'slave.py_tmpl')).read()
        template = template % {'python': sys.executable,
                               'paths': ',\n'.join(paths),
                               'slave_dir': location}

        script = join(bin_dir, '%s.py' % self.name)
        open(script, 'w').write(template)
        os.chmod(script, 0700)
        self.log('Generated script %s.' % script)
        return (filename, script)

    update = install

