#XXX Monkey patch buildbot ... waiting for patch to be commited in buildbot
import os
import types
from twisted.python import log, runtime
from buildbot.slave.commands import ShellCommandPP
from twisted.internet import reactor

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
            argv = [os.environ['COMSPEC'], '/c',
                    self.command.replace('/','\\')]
        else:
            # for posix, use /bin/sh. for other non-posix, well, doesn't
            # hurt to try
            argv = ['/bin/sh', '-c', self.command]
    else:
        if runtime.platformType  == 'win32':
            cmds = [cmd.replace('/','\\') for cmd in self.command]
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
