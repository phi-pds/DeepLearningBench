import os

from mparts.host import HostInfo, CHECKED, UNCHECKED
from mparts.manager import Task
from mparts.util import Progress
from support import ResultsProvider, SourceFileProvider, PrefetchDir, \
    FileSystem, SystemMonitor, PerfMonitor

__all__ = []

__all__.append("HelloLoad")
class HelloLoad(Task, ResultsProvider):
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
        return [os.path.join(self.helloPath, "run-hello")]

    def wait(self, m):
        logPath = self.host.getLogPath(self)
        #self.perfmon.stat_start()
        #self.perfmon.record_start()
        self.host.r.run(self.sysmon.wrap(self.__cmd("")),
                        stdout = logPath)
        # Get result
        log = self.host.r.readFile(logPath)
        self.sysmonOut = self.sysmon.parseLog(log)
        self.setResults(self.sysmonOut["time.real"], 
                        "host", "host", self.sysmonOut["time.real"])

        self.host.r.run(self.sysmon.wrap(self.__cmd("")),
                        stdout = logPath)
        log = self.host.r.readFile(logPath)
        self.sysmonOut = self.sysmon.parseLog(log)
        self.setResults(self.sysmonOut["time.real"], 
                        "host", "host", self.sysmonOut["time.real"])
 
        #self.perfmon.record_stop()
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
        m += fs
        helloPath = os.path.join(cfg.benchRoot, "hello")
        sysmon = SystemMonitor(host)
        m += sysmon
        perfmon = PerfMonitor(host)
        m += perfmon
        countcore = [1, 2, 4, 8, 15, 30, 45, 60, 75, 90, 105, 120]
        for trial in range(cfg.trials):
            m += HelloLoad(host, trial, helloPath, cfg.cores, sysmon, perfmon)
        m.run()

__all__.append("runner")
runner = HelloRunner()
