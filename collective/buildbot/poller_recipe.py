# -*- coding: utf-8 -*-

from collective.buildbot.recipe import BaseRecipe

import logging

class Poller(BaseRecipe):

    config_dir = 'pollers'

    def install(self):
        """generates .cfg files"""
        files = []
        globs = {}

        # poller values
        for key, value in self.options.items():
            globs[key] = value

        for k, v in (('vcs', 'svn'),
                     ('repository', ''),
                     ('poll-interval', '60'),
                     ('poll-interval', '60'),
                     ('hist-max', '100'),
                     ('svn-binary', 'svn'),
                     ):
            globs.setdefault(k, v)

        globs.pop('recipe')

        files.append(self.write_config(self.name, **{'poller':globs}))

        return files

    update = install

class Pollers(BaseRecipe):

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
        for i, url in enumerate(repositories):
            options['repository'] = url

            if len(repositories) > 1:
                name = '%s_%s' % (self.name, i)
            else:
                name = self.name

            p = Poller(self.buildout, name, options)
            files.extend(p.install())

        return files

    update = install
