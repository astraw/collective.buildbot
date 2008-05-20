# -*- coding: utf-8 -*-
from os.path import join
from collective.buildbot.recipe import BaseRecipe

class Project(BaseRecipe):
    """Buildout recipe to generate a project configuration file for a
    buildbot project.
    """

    config_dir = 'projects'

    def install(self):
        """generates .cfg files"""
        files = []
        project = self.name
        globs = dict(name=self.name)

        # default values in buildout section
        valid_args = ('mail-host', 'email-notification-sender',
                      'email-notification-recipients',)
        for key, value in self.buildout['buildout'].items():
            if key in valid_args:
                globs[key] = value

        # project values
        globs.update(dict(self.options.items()))
        globs.pop('recipe', '')

        for k, v in (('vcs', 'svn'),
                     ('mail-host', 'localhost'),
                     ('repository', ''),
                     ('email-notification-sender', ''),
                     ('email-notification-recipient', ''),
                     ('test-sequence', '\n'.join([join('bin', 'test --exit-with-status')])),
                     ):
            globs.setdefault(k, v)

        if 'build-sequence' not in globs:
            globs['build-sequence'] = '\n'.join(
                ['python bootstrap.py',
                 join('bin', 'buildout')])

        if globs['vcs'] == 'git':
            globs.setdefault('branch', 'master')

        files.append(self.write_config(project, **{'project':globs}))

        return files

    update = install

class Projects(BaseRecipe):
    """Deprecated"""

    def install(self):
        options = dict([(k,v) for k,v in self.options.items()])
        projects = options.pop('projects')
        projects = projects.splitlines()
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

    update = install
