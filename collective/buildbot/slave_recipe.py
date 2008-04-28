# -*- coding: utf-8 -*-
"""Recipe devserver"""
import sys
import os
import glob
import shutil
from os.path import join
import zc.buildout
import zc.recipe.egg
import virtualenv

recipe_dir = os.path.realpath(os.path.dirname(__file__))

def _log(msg):
    print msg

class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        eggs = zc.recipe.egg.Eggs(buildout, 'eggs', dict(eggs='collective.buildbot'))
        options['bin-directory'] = buildout['buildout']['bin-directory']
        options['scripts'] = '' # suppress script generation.
        parts_dir = buildout['buildout']['parts-directory']
        options['location'] = join(parts_dir, self.name)
        _, self.ws = eggs.working_set()

    def create_virtualenv(self, location):
        old = sys.argv
        try:
            sys.argv = ['iw_buildbot', '--no-site-packages', location]
            from virtualenv import main
            main()
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

        template = open(join(recipe_dir, 'slave.tac_tmpl')).read()
        template = template % data 
        filename = join(location, 'buildbot.tac')
        open(filename, 'w').write(template)
        _log('Generated script %s.' % filename) 
        
        # add the buildbot script
        bin_dir = self.options['bin-directory'] 
        paths = ["'%s'" % d.location for d in self.ws]
        template = open(join(recipe_dir, 'slave.py_tmpl')).read()
        template = template % {'python': sys.executable,
                               'paths': ',\n'.join(paths),
                               'slave_dir': location}

        script = join(bin_dir, '%s.py' % self.name)
        open(script, 'w').write(template)
        os.chmod(script, 0700)
        _log('Generated script %s.' % script)
        return (filename, script)
        
    def update(self):
        """Updater"""
        pass
