# -*- coding: utf-8 -*-
import os
import sys
import glob
import shutil
import virtualenv
import subprocess
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
        is_win = (sys.platform == 'win32')
        is_cygwin = (sys.platform == 'cygwin')
        executable = (is_win or is_cygwin) and 'python.exe' or 'python'
        binFolder = is_win and 'Scripts' or 'bin'
        binLocation = join(location, binFolder)

        if is_cygwin:
            # Virtualenv doesn't work on cygwin, but create a
            # bin/python using the one of buildout
            buildoutExecutable = self.buildout['buildout']['executable']
            if not buildoutExecutable.endswith('exe'):
                buildoutExecutable += '.exe'
            unixBinLocation = join(location, 'bin')
            if not os.path.isfile(join(unixBinLocation, executable)):
                if not os.path.exists(unixBinLocation):
                    os.mkdir(unixBinLocation)
                os.symlink(buildoutExecutable,
                           join(unixBinLocation, executable))
        else:
            old = sys.argv
            try:
                sys.argv = ['virtualenv', '--no-site-packages', location]
                virtualenv.main()
                if 'eggs' in self.options:
                    eggs = [e for e in self.options['eggs'].split('\n') if e]
                    subprocess.call([join(binLocation, 'easy_install'),] + eggs)
            finally:
                sys.argv = old

        if is_win:
            # On windows, add a bin/python
            unixBinLocation = join(location, 'bin')
            if not os.path.isfile(join(unixBinLocation, executable)):
                pythons = glob.glob(join(binLocation, 'python*'))
                if not os.path.exists(unixBinLocation):
                    os.mkdir(unixBinLocation)
                shutil.copyfile(pythons[0],
                                join(unixBinLocation, executable))


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

