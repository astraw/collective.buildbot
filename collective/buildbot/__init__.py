#XXX Monkey patch buildbot ... waiting for patch to be commited in buildbot
import os
import time
import types
from twisted.python import log, runtime
from buildbot.slave.commands import ShellCommandPP
from twisted.internet import reactor
from twisted.python import log

import pkg_resources

def ShellCommand_describe(self, done=False):
    """Return a list of short strings to describe this step, for the
    status display. This uses the first few words of the shell command.
    You can replace this by setting .description in your subclass, or by
    overriding this method to describe the step better.

    @type  done: boolean
    @param done: whether the command is complete or not, to improve the
                 way the command is described. C{done=False} is used
                 while the command is still running, so a single
                 imperfect-tense verb is appropriate ('compiling',
                 'testing', ...) C{done=True} is used when the command
                 has finished, and the default getText() method adds some
                 text, so a simple noun is appropriate ('compile',
                 'tests' ...)
    """

    if done and self.descriptionDone is not None:
        return list(self.descriptionDone)
    if self.description is not None:
        return list(self.description)

    properties = self.build.getProperties()
    words = self.command
    if isinstance(words, (str, unicode)):
        words = words.split()
    # render() each word to handle WithProperties objects
    words = properties.render(words)
    if len(words) < 1:
        return ["???"]
    if len(words) == 1:
        return ["'%s'" % words[0]]
    if len(words) == 2:
        return ["'%s" % words[0], "%s'" % words[1]]
    return ["'%s" % words[0], "%s" % words[1], "...'"]

from buildbot.steps.shell import WarningCountingShellCommand
def Test_describe(self, done=False):
    description = WarningCountingShellCommand.describe(self, done)
    if done:
        if self.step_status.hasStatistic('tests-total'):
            total = self.step_status.getStatistic("tests-total", 0)
            failed = self.step_status.getStatistic("tests-failed", 0)
            passed = self.step_status.getStatistic("tests-passed", 0)
            warnings = self.step_status.getStatistic("tests-warnings", 0)
            if not total:
                total = failed + passed + warnings

            if total:
                description.append('%d tests' % total)
            if passed:
                description.append('%d passed' % passed)
            if warnings:
                description.append('%d warnings' % warnings)
            if failed:
                description.append('%d failed' % failed)
    return description

if pkg_resources.get_distribution('buildbot').version == '0.7.9':
    # Monkey patch a fix for http://buildbot.net/trac/ticket/347 which is a bug in
    # 0.7.9. Once 0.7.10 is released these monkey patches should be removed.
    from buildbot.steps import shell
    shell.ShellCommand.describe = ShellCommand_describe
    shell.Test.describe = Test_describe
    log.msg('Monkey patched buildbot.steps.shell.ShellCommand.describe')
    log.msg('Monkey patched buildbot.steps.shell.Test.describe')
    del shell

def _startCommand(self):
    # ensure workdir exists
    if not os.path.isdir(self.workdir):
        os.makedirs(self.workdir)
    log.msg("ShellCommand._startCommand")
    if self.notreally:
        self.sendStatus({'header': "command '%s' in dir %s" % \
                         (self.command, self.workdir)})
        self.sendStatus({'header': "(not really)\n"})
        self.finished(None, 0)
        return

    self.pp = ShellCommandPP(self)

    if type(self.command) in types.StringTypes:
        if runtime.platformType  == 'win32':
            if '//' not in self.command:
                self.command = self.command.replace('/','\\')
            argv = [os.environ['COMSPEC'], '/c', self.command]
        else:
            # for posix, use /bin/sh. for other non-posix, well, doesn't
            # hurt to try
            argv = ['/bin/sh', '-c', self.command]
    else:
        if runtime.platformType  == 'win32':
            cmds = []
            for cmd in self.command:
                if '//' not in cmd:
                    cmds.append(cmd.replace('/','\\'))
                else:
                    cmds.append(cmd)
            argv = [os.environ['COMSPEC'], '/c'] + list(cmds)
        else:
            argv = self.command

    # self.stdin is handled in ShellCommandPP.connectionMade

    # first header line is the command in plain text, argv joined with
    # spaces. You should be able to cut-and-paste this into a shell to
    # obtain the same results. If there are spaces in the arguments, too
    # bad.
    msg = " ".join(argv)
    log.msg(" " + msg)
    self.sendStatus({'header': msg+"\n"})

    # then comes the secondary information
    msg = " in dir %s" % (self.workdir,)
    if self.timeout:
        msg += " (timeout %d secs)" % (self.timeout,)
    log.msg(" " + msg)
    self.sendStatus({'header': msg+"\n"})

    msg = " watching logfiles %s" % (self.logfiles,)
    log.msg(" " + msg)
    self.sendStatus({'header': msg+"\n"})

    # then the argv array for resolving unambiguity
    msg = " argv: %s" % (argv,)
    log.msg(" " + msg)
    self.sendStatus({'header': msg+"\n"})

    # then the environment, since it sometimes causes problems
    msg = " environment:\n"
    env_names = self.environ.keys()
    env_names.sort()
    for name in env_names:
        msg += "  %s=%s\n" % (name, self.environ[name])
    log.msg(" environment: %s" % (self.environ,))
    self.sendStatus({'header': msg})

    if self.initialStdin:
        msg = " writing %d bytes to stdin" % len(self.initialStdin)
        log.msg(" " + msg)
        self.sendStatus({'header': msg+"\n"})

    if self.keepStdinOpen:
        msg = " leaving stdin open"
    else:
        msg = " closing stdin"
    log.msg(" " + msg)
    self.sendStatus({'header': msg+"\n"})

    msg = " using PTY: %s" % bool(self.usePTY)
    log.msg(" " + msg)
    self.sendStatus({'header': msg+"\n"})

    # this will be buffered until connectionMade is called
    if self.initialStdin:
        self.pp.writeStdin(self.initialStdin)
    if not self.keepStdinOpen:
        self.pp.closeStdin()

    # win32eventreactor's spawnProcess (under twisted <= 2.0.1) returns
    # None, as opposed to all the posixbase-derived reactors (which
    # return the new Process object). This is a nuisance. We can make up
    # for it by having the ProcessProtocol give us their .transport
    # attribute after they get one. I'd prefer to get it from
    # spawnProcess because I'm concerned about returning from this method
    # without having a valid self.process to work with. (if kill() were
    # called right after we return, but somehow before connectionMade
    # were called, then kill() would blow up).
    self.process = None
    self.startTime = time.time()
    p = reactor.spawnProcess(self.pp, argv[0], argv,
                             self.environ,
                             self.workdir,
                             usePTY=self.usePTY)
    # connectionMade might have been called during spawnProcess
    if not self.process:
        self.process = p

    # connectionMade also closes stdin as long as we're not using a PTY.
    # This is intended to kill off inappropriately interactive commands
    # better than the (long) hung-command timeout. ProcessPTY should be
    # enhanced to allow the same childFDs argument that Process takes,
    # which would let us connect stdin to /dev/null .

    if self.timeout:
        self.timer = reactor.callLater(self.timeout, self.doTimeout)

    for w in self.logFileWatchers:
        w.start()

from buildbot.slave import commands
commands.ShellCommand._startCommand = _startCommand

#
# patching SVN so it can take username/password
#
from buildbot.slave.commands import SourceBase, getCommand, ShellCommand

def SVN_setup(self, args):
    SourceBase.setup(self, args)
    self.vcexe = getCommand("svn")
    self.svnurl = args['svnurl']
    self.sourcedata = "%s\n" % self.svnurl
    self.username = args.get("username", None) 
    self.password = args.get("password", None) 

commands.SVN.setup = SVN_setup

def SVN_doVCUpdate(self):
    revision = self.args['revision'] or 'HEAD'
    # update: possible for mode in ('copy', 'update')
    d = os.path.join(self.builder.basedir, self.srcdir)
    command = [self.vcexe, 'update', '--revision', str(revision),
            '--non-interactive', '--no-auth-cache']
    if self.username:
        command += ['--username', self.username]
    if self.password: 
        command += ['--password', self.password] 

    c = ShellCommand(self.builder, command, d,
                    sendRC=False, timeout=self.timeout,
                    keepStdout=True)
    self.command = c
    return c.start()

commands.SVN.doVCUpdate = SVN_doVCUpdate

def SVN_doVCFull(self):
    revision = self.args['revision'] or 'HEAD'
    d = self.builder.basedir
    if self.mode == "export":
        command = [self.vcexe, 'export', '--revision', str(revision),
                '--non-interactive', '--no-auth-cache']
    else:
        # mode=='clobber', or copy/update on a broken workspace
        command = [self.vcexe, 'checkout', '--revision', str(revision),
                '--non-interactive', '--no-auth-cache']
    
    if self.username: 
        command += ['--username', self.username] 
    if self.password: 
        command += ['--password', self.password]
    
    command += [self.svnurl, self.srcdir]

    c = ShellCommand(self.builder, command, d,
                    sendRC=False, timeout=self.timeout,
                    keepStdout=True)
    self.command = c
    return c.start()

commands.SVN.doVCFull = SVN_doVCFull

from buildbot import steps
from buildbot.steps.source import Source

def SVNStep__init__(self, svnurl=None, baseURL=None, defaultBranch=None,
                    directory=None, username=None,
                    password=None, **kwargs):
       
        if not kwargs.has_key('workdir') and directory is not None:
            # deal with old configs
            warn("Please use workdir=, not directory=", DeprecationWarning)
            kwargs['workdir'] = directory

        self.svnurl = svnurl
        self.baseURL = baseURL
        self.branch = defaultBranch
        self.username = username
        self.password = password

        Source.__init__(self, **kwargs)
        self.addFactoryArguments(svnurl=svnurl,
                                 baseURL=baseURL,
                                 defaultBranch=defaultBranch,
                                 directory=directory,
                                 username=username,
                                 password=password
                                 )

        if not svnurl and not baseURL:
            raise ValueError("you must use exactly one of svnurl and baseURL")

steps.source.SVN.__init__ = SVNStep__init__ 

from buildbot.process.buildstep import LoggedRemoteCommand
from buildbot.interfaces import BuildSlaveTooOldError
from twisted.python import log 

def SVNStep_startVC(self, branch, revision, patch):
    warnings = []
    slavever = self.slaveVersion("svn", "old")
    if not slavever:
        m = "slave does not have the 'svn' command"
        raise BuildSlaveTooOldError(m)

    if self.slaveVersionIsOlderThan("svn", "1.39"):
        if (branch != self.branch
            and self.args['mode'] in ("update", "copy")):
            m = ("This buildslave (%s) does not know about multiple "
                    "branches, and using mode=%s would probably build the "
                    "wrong tree. "
                    "Refusing to build. Please upgrade the buildslave to "
                    "buildbot-0.7.0 or newer." % (self.build.slavename,
                                                self.args['mode']))
            raise BuildSlaveTooOldError(m)

    if slavever == "old":
        if self.args['mode'] in ("clobber", "copy"):
            warnings.append("WARNING: this slave can only do SVN updates"
                            ", not mode=%s\n" % self.args['mode'])
            log.msg("WARNING: this slave only does mode=update")
        if self.args['mode'] == "export":
            raise BuildSlaveTooOldError("old slave does not have "
                                        "mode=export")
        self.args['directory'] = self.args['workdir']
        if revision is not None:
            m = ("WARNING: old slave can only update to HEAD, not "
                    "revision=%s" % revision)
            log.msg(m)
            warnings.append(m + "\n")
        revision = "HEAD" # interprets this key differently
        if patch:
            raise BuildSlaveTooOldError("old slave can't do patch")

    if self.svnurl:
        assert not branch # we need baseURL= to use branches
        self.args['svnurl'] = self.svnurl
    else:
        self.args['svnurl'] = self.baseURL + branch
    self.args['revision'] = revision
    self.args['patch'] = patch
    if self.username: 
        self.args['username'] = self.username
    if self.password:
        self.args['password'] = self.password 
    revstuff = []
    if branch is not None and branch != self.branch:
        revstuff.append("[branch]")
    if revision is not None:
        revstuff.append("r%s" % revision)
    if patch is not None:
        revstuff.append("[patch]")
    self.description.extend(revstuff)
    self.descriptionDone.extend(revstuff)

    cmd = LoggedRemoteCommand("svn", self.args)
    self.startCommand(cmd, warnings)

steps.source.SVN.startVC = SVNStep_startVC

#
# patching twisted
#
import sys
if sys.platform == 'win32':
    from twisted.internet import main
    key = 'twisted.internet.reactor'

    if sys.modules.has_key(key):
        if sys.modules[key] != reactor:
            raise AssertionError('reactor already installed: %s' % sys.modules[key])
        
    def _installReactor(reactor):
        import twisted.internet
        import sys
        twisted.internet.reactor = reactor
	sys.modules[key] = reactor
    main.installReactor = _installReactor

