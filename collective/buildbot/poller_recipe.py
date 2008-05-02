# -*- coding: utf-8 -*-
import sys
import os
import urlparse
from os.path import join
from collective.buildbot.recipe import BaseRecipe


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
                     ('base-url', ''),
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
        urls = options.pop('base-urls')
        urls = urls.split('\n')
        urls = [p.strip() for p in urls if p.strip()]
        files = []
        for i, url in enumerate(urls):
            options['base-url'] = url
            p = Poller(self.buildout, 'poller_%i' % i, options)
            files.extend(p.install())
        return files

    update = install
