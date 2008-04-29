# -*- coding: utf-8 -*-
import sys
import os
import urlparse
from os.path import join
from Cheetah.Template import Template as CheetahTemplate
from collective.buildbot.recipe import BaseRecipe

class Project(BaseRecipe):

    def install(self):
        """generates .cfg files"""
        files = []
        def _cmds(seq):
            cmds = [cmd.strip() for cmd in seq.split('\n')
                   if cmd.strip() != '']
            return '\n' + '    \n'.join(['    %s' % cmd for cmd in cmds])
        project = self.name
        template = open(join(self.recipe_dir, 'project.cfg_tmpl')).read()
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
        for key, value in self.options.items():
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
        del search_list['recipe']

        globs = dict(name=project,
                     project=config_dict(search_list),
                     poller=[])

        if poller:
            poller_conf = self.buildout[poller]
            globs['poller'] = config_dict(poller_conf)


        template = CheetahTemplate(template,
                                   searchList=[globs])

        target = join(self.projects_directory, '%s.cfg' % project)

        if not os.path.isdir(self.projects_directory):
            os.mkdir(self.projects_directory)

        open(target, 'w').write(str(template))
        files.append(target)
        self.log('Generated project config %r.' % target)
        return tuple()

    update = install

class Projects(BaseRecipe):

    def install(self):
        options = dict([(k,v) for k,v in self.options.items()])
        projects = options.pop('projects')
        projects = projects.split('\n')
        projects = [p.strip() for p in projects if p.strip()]
        base_url = options.pop('base-url')
        if 'branch' in options:
            branch = options.pop('branch')
        else:
            branch = 'trunk'
        files = []
        for project in projects:
            options['base-url'] = urlparse.urljoin(
                                    base_url, '%s/%s' % (project, branch))
            p = Project(self.buildout, project, options)
            files.extend(p.install())
        return files

