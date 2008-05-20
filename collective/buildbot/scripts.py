# -*- coding: utf-8 -*-
import os
import sys
import buildbot.scripts.runner

def main(location, config_file):
    if config_file:
        os.environ['BUILDBOT_CONFIG'] = config_file
    if len(sys.argv) > 1 and sys.argv[1] in ('stop', 'start', 'restart'):
        # automatically include the path to buildbot.tac
        cmd = sys.argv[-1]
        sys.argv = [sys.argv[0], cmd, location]
        buildbot.scripts.runner.run()

