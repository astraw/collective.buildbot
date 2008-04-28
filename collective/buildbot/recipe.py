# -*- coding: utf-8 -*-
import os
import sys
import shutil
import virtualenv
import zc.recipe.egg
from os.path import join

class BaseRecipe(object):

    def log(self, msg):
        print msg

    recipe_dir = os.path.dirname(__file__)

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        self.location = join(buildout['buildout']['parts-directory'], self.name)
        self.projects_directory = join(buildout['buildout']['parts-directory'], 'projects')
        eggs = zc.recipe.egg.Eggs(buildout, 'collective.buildbot', dict(eggs='collective.buildbot'))
        _, self.ws = eggs.working_set()

    def create_virtualenv(self, location):
        old = sys.argv
        try:
            sys.argv = ['iw_buildbot', '--no-site-packages', location]
            virtualenv.main()
        finally:
            sys.argv = old

        is_posix = sys.platform != 'win32'
        executable = is_posix and 'python' or 'python.exe'
        if not os.path.isfile(join(location, 'bin', executable)):
            pythons = glob.glob(join(location, 'bin', 'python*'))
            shutil.copyfile(pythons[0],
                            join(location, 'bin', executable))

            if is_posix:
                os.chmod(join(location, 'bin', executable), 0755)

