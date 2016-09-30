from mparts.manager import Task
from mparts.host import HostInfo, CHECKED, UNCHECKED
from mparts.util import Progress
from support import ResultsProvider, SourceFileProvider, SetCPUs, PrefetchDir, \
    FileSystem, SystemMonitor

import os

__all__ = []

__all__.append("HelloLoad")
class HelloLoad(Task, ResultsProvider, SourceFileProvider):
    __info__ = ["host", "*sysmonOut"]

    def __init__(self, host, trial, cores, sysmon):
        Task.__init__(self, host = host, trial = trial)
        ResultsProvider.__init__(self, cores)
        self.host = host
        self.sysmon = sysmon

    def __cmd(self, target):
        return ["ls"]

    def wait(self, m):
        logPath = self.host.getLogPath(self)

        # Copy configuration file
        # Build for real
        #
        # XXX If we want to eliminate the serial startup, monitor
        # starting with "  CHK include/generated/compile.h" or maybe
        # with the first "  CC" line.
        self.host.r.run(self.sysmon.wrap(self.__cmd("")),
                        stdout = logPath)

        # Get result
        log = self.host.r.readFile(logPath)
        self.sysmonOut = self.sysmon.parseLog(log)
        self.setResults(1, "build", "builds", self.sysmonOut["time.real"])

class HelloRunner(object):
    def __str__(self):
        return "Hello"

    @staticmethod
    def run(m, cfg):
        host = cfg.primaryHost
        m += host
        m += HostInfo(host)
        fs = FileSystem(host, cfg.fs, clean = True)
        m += fs
        # It's really hard to predict what make will access, so we
        # prefetch the whole source tree.  This, combined with the
        # pre-build of init/main.o, eliminates virtually all disk
        # reads.  For the rest, we'll just have to rely on multiple
        # trials or at least multiple configurations to cache.
        sysmon = SystemMonitor(host)
        m += sysmon
        for trial in range(cfg.trials):
            m += HelloLoad(host, trial, cfg.cores, sysmon)
        # m += cfg.monitors
        m.run()

__all__.append("runner")
runner = HelloRunner()
