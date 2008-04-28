# -*- coding: utf-8 -*-
"""Recipe buildmaster"""
import sys
import os
from os.path import join
import shutil
import zc.buildout
import zc.recipe.egg
from Cheetah.Template import Template as CheetahTemplate
import virtualenv

recipe_dir = os.path.dirname(__file__)

def _log(msg):
    print msg

class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        eggs = zc.recipe.egg.Eggs(buildout, 'collective.buildbot', dict(eggs='collective.buildbot'))
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

    def install(self):
        """Installer"""
        location = self.options['location']
        working_directory = location
        projects_directory = join(location, 'projects')
        files = []

        # creates the dir
        if not os.path.exists(location):
            os.mkdir(location)
        if not os.path.exists(projects_directory):
            os.mkdir(projects_directory)

        self.create_virtualenv(location)

        # adds buildbot.tac
        template = open(join(recipe_dir, 'buildbot.tac_tmpl')).read()
        template = template % {'base_dir': working_directory}
        buildbot_tac = join(location, 'buildbot.tac')
        open(buildbot_tac, 'w').write(str(template))
        _log('Generated script %s.' % buildbot_tac)
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

        search_list['projects_directory'] = projects_directory
        search_list['slaves'] = buildbot_slaves
        search_list.setdefault('allow_force', 'false')
        template = join(recipe_dir, 'buildbot.cfg_tmpl')
        template = CheetahTemplate(open(template).read(),
                                   searchList=[search_list])
        buildbot_cfg = join(location, 'buildbot.cfg')
        open(buildbot_cfg, 'w').write(str(template))
        _log('Generated script %s.' % buildbot_cfg)
        files.append(buildbot_cfg)

        # generates buildbot projects section
        projects = [proj.strip() for proj in
                    self.options.get('projects', '').split()
                    if proj.strip() != '']

        cfgs = self._generate_projects(projects_directory, projects)
        files.extend(cfgs)

        # generates the buildbot script
        bin_dir = self.options['bin-directory']
        paths = ["'%s'" % d.location for d in self.ws]
        template = open(join(recipe_dir, 'buildbot.py_tmpl')).read()
        template = template % {'python': sys.executable,
                               'paths': ',\n'.join(paths),
                               'config_file': buildbot_cfg,
                               'builbot_dir': location}

        script_name = join(bin_dir, '%s.py' % self.name)
        open(script_name, 'w').write(template)
        os.chmod(script_name, 0700)
        _log('Generated script %s.' % script_name)
        files.append(script_name)

        return tuple(files)

    def _generate_projects(self, project_dir, projects):
        """generates .cfg files"""
        files = []
        def _cmds(seq):
            cmds = [cmd.strip() for cmd in seq.split('\n')
                   if cmd.strip() != '']
            return '\n' + '    \n'.join(['    %s' % cmd for cmd in cmds])

        for project in projects:
            if project not in self.buildout:
                continue
            self.buildout[project]['name'] = project
            template = open(join(recipe_dir, 'project.cfg_tmpl')).read()
            search_list = {}
            globs = {}

            def normalyse_option(option):
                return option.replace('\n', '\n    ')

            # default values in buildout section
            valid_args = ('mail-host', 'email-notification-sender',
                          'email-notification-recipients',)
            for key, value in self.buildout['buildout'].items():
                if key in valid_args:
                    search_list[key] = normalyse_option(value)

            # project values
            for key, value in self.buildout[project].items():
                search_list[key] = normalyse_option(value)

            for f, v in (('vcs', 'svn'),
                         ('branch', ''),
                         ('base-url', ''),
                         ('mail-host', 'localhost'),
                         ('email-notification-sender', ''),
                         ('email-notification-recipient', '')):
                if f not in search_list:
                    search_list[f] = v

            if 'test-sequence' not in search_list:
                search_list['test-sequence'] = \
                    '\n'.join([join('bin', 'test --exit-with-status')])

            search_list['test-sequence'] = _cmds(search_list['test-sequence'])
            if 'build-sequence' not in search_list:
                search_list['build-sequence'] = '\n'.join(
                                                 ['python bootstrap.py',
                                                  join('bin', 'buildout')])
            search_list['build-sequence'] = _cmds(search_list['build-sequence'])
            search_list.setdefault('repository', '')

            def config_dict(d):
                return [dict(key=k, value=d[k]) for k in sorted(d)]

            poller = search_list.get('poller', None)
            if 'poller' in search_list:
                del search_list['poller']

            globs = dict(name=project,
                         project=config_dict(search_list),
                         poller=[])

            if poller:
                poller_conf = self.buildout[poller]
                globs['poller'] = config_dict(poller_conf)


            template = CheetahTemplate(template,
                                       searchList=[globs])

            target = join(project_dir, '%s.cfg' % project)
            open(target, 'w').write(str(template))
            files.append(target)
            _log('Generated script %s.' % target)
        return files

    def update(self):
        """Updater"""
        pass
