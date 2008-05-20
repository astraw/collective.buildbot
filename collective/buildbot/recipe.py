# -*- coding: utf-8 -*-
import os
import sys
import glob
import shutil
import virtualenv
from os.path import join
from ConfigParser import ConfigParser

class BaseRecipe(object):

    config_dir = ''

    def log(self, msg):
        print msg

    recipe_dir = os.path.dirname(__file__)

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        self.location = join(buildout['buildout']['parts-directory'], self.name)
        dirname = join(self.buildout['buildout']['parts-directory'],
                        self.config_dir or self.name)
        if not os.path.isdir(dirname):
            os.mkdir(dirname)

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

    def write_config(self, name, **kwargs):
        config = ConfigParser()
        for section, options in sorted(kwargs.items(), reverse=True):
            config.add_section(section)
            for key, value in sorted(options.items(), reverse=True):
                config.set(section, key, value)
        filename = join(self.buildout['buildout']['parts-directory'],
                        self.config_dir or self.name, '%s.cfg' % name)
        fd = open(filename, 'w')
        config.write(fd)
        fd.close()
        self.log('Generated config %r.' % filename)
        return filename

