# -*- coding: utf-8 -*-
"""Recipe buildmaster"""
import sys
import os
from os.path import join
import shutil
import zc.buildout
import zc.recipe.egg
from Cheetah.Template import Template as CheetahTemplate
from collective.buildbot.recipe import BaseRecipe
import virtualenv

class Recipe(BaseRecipe):
    """zc.buildout recipe"""

    def install(self):
        """Installer"""
        location = self.location
        working_directory = location
        files = []

        # creates the dir
        if not os.path.exists(location):
            os.mkdir(location)
        if not os.path.exists(self.projects_directory):
            os.mkdir(self.projects_directory)

        self.create_virtualenv(location)

        # adds buildbot.tac
        template = open(join(self.recipe_dir, 'buildbot.tac_tmpl')).read()
        template = template % {'base_dir': working_directory}
        buildbot_tac = join(location, 'buildbot.tac')
        open(buildbot_tac, 'w').write(str(template))
        self.log('Generated script %s.' % buildbot_tac)
        files.append(buildbot_tac)

        # generates the buildbot.cfg file
        slaves = self.options.get('slaves', '')
        slaves = [(slave.split()[0], slave.split()[1])
                  for slave in slaves.split('\n')
                  if slave.strip() != '']
        buildbot_slaves = [{'name': name, 'password': password}
                           for name, password in slaves]

        search_list = {}
        for key, value in self.options.items():
            if key == 'slaves':
                continue
            key = key.replace('-', '_')
            search_list[key] = value

        search_list['projects_directory'] = self.projects_directory
        search_list['slaves'] = buildbot_slaves
        search_list.setdefault('allow_force', 'false')
        template = join(self.recipe_dir, 'buildbot.cfg_tmpl')
        template = CheetahTemplate(open(template).read(),
                                   searchList=[search_list])
        buildbot_cfg = join(location, 'buildbot.cfg')
        open(buildbot_cfg, 'w').write(str(template))
        self.log('Generated script %s.' % buildbot_cfg)
        files.append(buildbot_cfg)

        # generates the buildbot script
        bin_dir = self.buildout['buildout']['bin-directory']
        paths = ["'%s'" % d.location for d in self.ws]
        template = open(join(self.recipe_dir, 'buildbot.py_tmpl')).read()
        template = template % {'python': sys.executable,
                               'paths': ',\n'.join(paths),
                               'config_file': buildbot_cfg,
                               'builbot_dir': location}

        script_name = join(bin_dir, '%s.py' % self.name)
        open(script_name, 'w').write(template)
        os.chmod(script_name, 0700)
        self.log('Generated script %s.' % script_name)
        files.append(script_name)

        return tuple()


    update = install
