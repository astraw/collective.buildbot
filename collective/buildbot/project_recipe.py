# -*- coding: utf-8 -*-
import sys
import os
import urlparse
from os.path import join
from collective.buildbot.recipe import BaseRecipe


class Project(BaseRecipe):

    def install(self):
        """generates .cfg files"""
        files = []
        project = self.name
        search_list = dict(name=self.name)
        globs = {}

        # default values in buildout section
        valid_args = ('mail-host', 'email-notification-sender',
                      'email-notification-recipients',)
        for key, value in self.buildout['buildout'].items():
            if key in valid_args:
                search_list[key] = value

        # project values
        for key, value in self.options.items():
            search_list[key] = value

        for k, v in (('vcs', 'svn'),
                     ('branch', 'trunk'),
                     ('base-url', ''),
                     ('mail-host', 'localhost'),
                     ('repository', ''),
                     ('email-notification-sender', ''),
                     ('email-notification-recipient', ''),
                     ('test-sequence', '\n'.join([join('bin', 'test --exit-with-status')])),
                     ('build-sequence', '\n'.join(
                                             ['python bootstrap.py',
                                              join('bin', 'buildout')])),
                     ):
            search_list.setdefault(k, v)

        search_list['branch'] = '%s/%s' % (self.name, search_list['branch'])

        poller = None
        if 'poller' in search_list:
            poller = search_list.pop('poller')

        globs = dict(project=search_list)

        if poller:
            poller_conf = self.buildout[poller]
            globs['poller'] = poller_conf

        if not os.path.isdir(self.projects_directory):
            os.mkdir(self.projects_directory)

        target = join(self.projects_directory, '%s.cfg' % project)
        files.append(self.write_config(target, **globs))

        return files

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
            options['base-url'] = base_url
            options['branch'] = branch
            p = Project(self.buildout, project, options)
            files.extend(p.install())
        return files

