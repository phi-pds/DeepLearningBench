import os

from mparts.host import HostInfo, CHECKED, UNCHECKED
from mparts.manager import Task
from mparts.util import Progress
from support import ResultsProvider, SourceFileProvider, SetCPUs, PrefetchDir, \
    FileSystem, SystemMonitor, PerfMonitor


__all__ = []

__all__.append("HelloLoad")
class HelloLoad(Task, ResultsProvider, SourceFileProvider):
    __info__ = ["host",  "trial", "helloPath", "*sysmonOut"]

    def __init__(self, host, trial, helloPath, cores, sysmon, perfmon):
        Task.__init__(self, host = host, trial = trial)
        ResultsProvider.__init__(self, cores)
        self.host = host
        self.trial = trial 
        self.sysmon = sysmon
        self.perfmon = perfmon
        self.helloPath = helloPath
        

    def __cmd(self, target):
        return [os.path.join(self.helloPath, "hello")]

    def wait(self, m):
        logPath = self.host.getLogPath(self)

        # Copy configuration file
        # Build for real
        #
        # XXX If we want to eliminate the serial startup, monitor
        # starting with "  CHK include/generated/compile.h" or maybe
        # with the first "  CC" line.
        #self.perfmon.stat_start()
        self.perfmon.record_start()
        self.host.r.run(self.sysmon.wrap(self.__cmd("")),
                        stdout = logPath)

        #self.host.r.run(self.perfmon.stop(),
        #                stdout = logPath)
        # Get result
        log = self.host.r.readFile(logPath)
        self.sysmonOut = self.sysmon.parseLog(log)
        self.setResults(1, "build", "builds", self.sysmonOut["time.real"])
        self.perfmon.record_stop()
        #self.perfmon.stat_stop()

class HelloRunner(object):
    def __str__(self):
        return "Hello"

    @staticmethod
    def run(m, cfg):
        host = cfg.primaryHost
        m += host
        m += HostInfo(host)
        fs = FileSystem(host, cfg.fs, clean = True)
        helloPath = os.path.join(cfg.benchRoot, "hello")
        m += fs
        # It's really hard to predict what make will access, so we
        # prefetch the whole source tree.  This, combined with the
        # pre-build of init/main.o, eliminates virtually all disk
        # reads.  For the rest, we'll just have to rely on multiple
        # trials or at least multiple configurations to cache.
        sysmon = SystemMonitor(host)
        m += sysmon
        perfmon = PerfMonitor(host)
        m += perfmon
        for trial in range(cfg.trials):
            m += HelloLoad(host, trial, helloPath, cfg.cores, sysmon, perfmon)
        # m += cfg.monitors
        m.run()

__all__.append("runner")
runner = HelloRunner()
