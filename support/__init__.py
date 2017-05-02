import sys, os, time, errno

from mparts.host import *
from mparts.manager import Task


__all__ = []

__all__.append("ResultsProvider")
class ResultsProvider(object):
    """A ResultsProvider is a marker interface searched for by the
    MOSBENCH analysis tools.  Every benchmark trial should produce one
    ResultsProvider object.  This records the number of cores, the
    number of units of work done, what those units are, and how long
    it took to do that work.  In addition, if the benchmark is using
    SystemMonitor, the analysis tools expect to find its logs results
    in the ResultsProvider subclass."""

    __info__ = ["cores", "result", "unit", "units", "real"]

    def __init__(self, cores):
        self.cores = cores

    def setResults(self, result, unit, units, real):
        """Set the results of this object.  result is the number of
        work units completed.  For job-oriented benchmarks, this
        should generally be 1.  unit and units are the name of a unit
        of work, in singular and plural form.  real is the number of
        seconds of real time elapsed while performing this work."""

        self.log("=> %g %s (%g secs, %g %s/sec/core)" %
                 (result, units, real, float(result)/real/self.cores, units))
        self.result = float(result)
        self.unit = unit
        self.units = units
        self.real = real

PREFETCH_CACHE = set()

__all__.append("PrefetchList")
class PrefetchList(Task, SourceFileProvider):
    __info__ = ["host", "filesPath"]

    def __init__(self, host, filesPath, reuse = False):
        Task.__init__(self, host = host, filesPath = filesPath)
        self.host = host
        self.filesPath = filesPath
        self.reuse = reuse

        self.__script = self.queueSrcFile(host, "prefetch")

    def start(self):
        if self.reuse:
            # XXX Is this actually useful?  Does it actually take any
            # time to re-fetch something that's already been
            # prefetched?
            if (self.host, self.filesPath) in PREFETCH_CACHE:
                return
            PREFETCH_CACHE.add((self.host, self.filesPath))

        self.host.r.run([self.__script, "-l"], stdin = self.filesPath)

__all__.append("PrefetchDir")
class PrefetchDir(Task, SourceFileProvider):
    __info__ = ["host", "topDir", "excludes"]

    def __init__(self, host, topDir, excludes = []):
        Task.__init__(self, host = host, topDir = topDir)
        self.host = host
        self.topDir = topDir
        self.excludes = excludes

        self.__script = self.queueSrcFile(host, "prefetch")

    def start(self):
        cmd = [self.__script, "-r"]
        for x in self.excludes:
            cmd.extend(["-x", x])
        self.host.r.run(cmd + [self.topDir])

__all__.append("FileSystem")
class FileSystem(Task, SourceFileProvider):
    __info__ = ["host", "fstype"]

    def __init__(self, host, fstype, clean = True):
        Task.__init__(self, host = host, fstype = fstype)
        self.host = host
        self.fstype = fstype
        self.__clean = clean
        assert '/' not in fstype
        self.path = "/tmp/mosbench/%s/" % fstype
        self.__script = self.queueSrcFile(host, "cleanfs")

    def start(self):
        # Check that the file system exists.  We check the mount table
        # instead of just the directory so we don't get tripped up by
        # stale mount point directories.
        mountCheck = self.path.rstrip("/")
        for l in self.host.r.readFile("/proc/self/mounts").splitlines():
            if l.split()[1].startswith(mountCheck):
                break
        else:
            raise ValueError(
                "No file system mounted at %s.  Did you run 'mkmounts %s' on %s?" %
                (mountCheck, self.fstype, self.host))

        # Clean
        if self.__clean:
            self.clean()

    def clean(self):
        self.host.r.run([self.__script, self.fstype])

__all__.append("waitForLog")
def waitForLog(host, logPath, name, secs, string):
    for retry in range(secs*2):
        try:
            log = host.r.readFile(logPath)
        except EnvironmentError, e:
            if e.errno != errno.ENOENT:
                raise
        else:
            if string in log:
                return
        time.sleep(0.5)
    raise RuntimeError("Timeout waiting for %s to start" % name)

# XXX Perhaps this shouldn't be a task at all.  It has to send a
# source file, but doesn't have any life-cycle.
__all__.append("SystemMonitor")
class SystemMonitor(Task, SourceFileProvider):
    __info__ = ["host"]

    def __init__(self, host):
        Task.__init__(self, host = host)
        self.host = host
        self.__script = self.queueSrcFile(host, "sysmon")

    def wrap(self, cmd, start = None, end = None):
        out = [self.__script]
        if start != None:
            out.extend(["-s", start])
        if end != None:
            out.extend(["-e", end])
        out.extend(cmd)
        return out

    def parseLog(self, log):
        """Parse a log produced by a sysmon-wrapped command, returning
        a dictionary of configuration values that should be
        incorporated into the calling object's configuration."""

        mine = [l for l in log.splitlines() if l.startswith("[TimeMonitor] ")]
        if len(mine) == 0:
            raise ValueError("No sysmon report found in log file")
        for i in range(len(mine)) :
            parts = mine[i].split()[1:]
            res = {}
            while parts:
                k, v = parts.pop(0), parts.pop(0)
                res["time." + k] = float(v)
        return res

__all__.append("ExplicitSystemMonitor")
class ExplicitSystemMonitor(SystemMonitor):
    def __init__(self, *args, **kwargs):
        SystemMonitor.__init__(self, *args, **kwargs)
        self.__p = None
        self.__gen = 0

    def start(self):
        assert self.__p == None
        cmd = self.wrap([], start = "start", end = "end")
        self.__logPath = self.host.getLogPath(self) + ".%d" % self.__gen
        self.__gen += 1
        self.__p = self.host.r.run(cmd, stdin = CAPTURE,
                                   stdout = self.__logPath,
                                   wait = False)

    def __term(self, check):
        if self.__p:
            self.__p.stdinClose()
            self.__p.wait(check)
            self.__p = None

    def stop(self):
        self.__term(True)

    def reset(self):
        self.__term(False)

    def startMonitor(self):
        self.__p.stdinWrite("start\n")

    def stopMonitor(self):
        self.__p.stdinWrite("end\n")
        # Force results out
        self.__term(True)
        # Get the results
        log = self.host.r.readFile(self.__logPath)
        # Start a new monitor, for multiple trials
        self.start()
        return self.parseLog(log)

__all__.append("PerfMonitor")
class PerfMonitor(Task, SourceFileProvider):
    __info__ = ["host"]

    def __init__(self, host):
        Task.__init__(self, host = host)
        self.host = host
        self.__gen = 0
        self.__script = self.queueSrcFile(host, "perfmon")

    def stat_start(self):
        self.__logPath = self.host.getLogPath(self) + ".perf.data.%d" % self.__gen
        print("PerfMonitor start")
        cmd = [self.__script, "stat_start", self.__logPath]
        self.__p = self.host.r.run(cmd, stdin = CAPTURE,
                                          wait = False)
       
    def stat_stop(self):
        self.__logPath = self.host.getLogPath(self) + ".perf.data.%d" % self.__gen
        self.__gen += 1
        print("PerfMonitor stop")
        cmd = [self.__script, "stat_stop", self.__logPath]
        self.__p = self.host.r.run(cmd, stdin = CAPTURE,
                                          wait = False)


    def record_start(self):
        self.__logPath = self.host.getLogPath(self) + ".perf.data.%d" % self.__gen
        print("PerfMonitor record start")
        cmd = [self.__script, "record_start", self.__logPath]
        self.__p = self.host.r.run(cmd, stdin = CAPTURE,
                                          wait = False)
       
    def record_stop(self):
        self.__logPath = self.host.getLogPath(self) + ".perf.data.%d" % self.__gen
        self.__gen += 1
        print("PerfMonitor record stop")
        cmd = [self.__script, "record_stop", self.__logPath]
        self.__p = self.host.r.run(cmd, stdin = CAPTURE,
                                          wait = False)
        self.__p.wait(True)
