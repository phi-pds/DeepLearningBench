from mparts.configspace import ConfigSpace
from mparts.host import Host
import sys
from support import perfLocked
import support.rsshash as rsshash

mk = ConfigSpace.mk
shared = ConfigSpace.unit()

knl = Host("MOSS", None)
shared *= mk(primaryHost = knl)
shared *= mk(benchRoot = "~/github/xeonphibench")
shared *= mk(fs = "tmpfs-separate")

shared *= mk(trials = 3)
shared *= mk(hotplug = True)
shared *= mk(cores = [4], nonConst = True)

import hello
hello = mk(benchmark = hello.runner, nonConst = True)

configSpace = hello.merge(shared)

if __name__ == "__main__":
    from mparts.manager import generateManagers
    from mparts.rpc import print_remote_exception
    import sys
    sys.excepthook = print_remote_exception
    for (m, cfg) in generateManagers("results", configSpace):
        cfg.benchmark.run(m, cfg)
