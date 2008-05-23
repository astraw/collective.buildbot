# -*- coding: utf-8 -*-
from os.path import join
from collective.buildbot.recipe import BaseRecipe

import logging

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
    """Multiple project support within a single buildout section.

    All configuration options will be shared among the projects with
    the exception of the repository. For Subversion repositories it is
    possible to define separate branches/tags. For Git and other vcs
    that use the ``branch`` option the branch will be shared also.
    """

    def install(self):
        options = dict([(k,v) for k,v in self.options.items()])
        log = logging.getLogger(self.name)
        
        # BBB
        if 'repository' in options:
            log.info('The "repository" option is deprecated in favor '
                     'of "repositories". Please update your buildout configuration.')
            options['repositories'] = options.pop('repository')

        repositories = [r.strip() for r
                        in options.pop('repositories', '').splitlines()
                        if r.strip()]

        files = []
        for idx, repository in enumerate(repositories):
            if len(repositories) > 1:
                name = '%s_%s' % (self.name, idx)
            else:
                name = self.name

            options['repository'] = repository
            p = Project(self.buildout, name, options)
            files.extend(p.install())

        return files

    update = install
