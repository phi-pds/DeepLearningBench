import sys

from mparts.configspace import ConfigSpace
from mparts.host import Host
import support.rsshash as rsshash


mk = ConfigSpace.mk
shared = ConfigSpace.unit()

knl = Host("MOSS", None)
shared *= mk(primaryHost = knl)
shared *= mk(benchRoot = "~/github/DeepLearningBench")
shared *= mk(fs = "tmpfs")

shared *= mk(trials = 1)
shared *= mk(hotplug = True)
# shared *= mk(cores = [1], nonConst = True)
shared *= mk(cores = [120], nonConst = True)

import hello
hello = mk(benchmark = hello.runner, nonConst = True)

import mnist
mnist = mk(benchmark = mnist.runner, nonConst = True)


##################################################################
# Complete configuration
#

# XXX Hmm.  Constant analysis is space-global right now, so combining
# spaces for different benchmarks may give odd results.

# We compute the product of the benchmark configurations with the
# shared configuration instead of the other way around so that we will
# perform all configurations of a given benchmark before moving on to
# the next, even if the shared configuration space contains more than
# one configuration.  Furthermore, instead of computing the regular
# product, we compute a "merge" product, where assignments from the
# left will override assignments to the same variables from the right.
#configSpace = (hello + mnist).merge(shared)
configSpace = (hello).merge(shared)

if __name__ == "__main__":
    from mparts.manager import generateManagers
    from mparts.rpc import print_remote_exception
    import sys
    sys.excepthook = print_remote_exception
    for (m, cfg) in generateManagers("results", configSpace):
        cfg.benchmark.run(m, cfg)

