import os

import cPickle as pickle


__all__ = ["Experiment", "experiments", "series", "filterInfo", "the"]

# os.walk from Python 2.6, which adds support for followlinks.
def walk(top, topdown=True, onerror=None, followlinks=False):
    """Directory tree generator.

    For each directory in the directory tree rooted at top (including top
    itself, but excluding '.' and '..'), yields a 3-tuple

        dirpath, dirnames, filenames

    dirpath is a string, the path to the directory.  dirnames is a list of
    the names of the subdirectories in dirpath (excluding '.' and '..').
    filenames is a list of the names of the non-directory files in dirpath.
    Note that the names in the lists are just names, with no path components.
    To get a full path (which begins with top) to a file or directory in
    dirpath, do os.path.join(dirpath, name).

    If optional arg 'topdown' is true or not specified, the triple for a
    directory is generated before the triples for any of its subdirectories
    (directories are generated top down).  If topdown is false, the triple
    for a directory is generated after the triples for all of its
    subdirectories (directories are generated bottom up).

    When topdown is true, the caller can modify the dirnames list in-place
    (e.g., via del or slice assignment), and walk will only recurse into the
    subdirectories whose names remain in dirnames; this can be used to prune
    the search, or to impose a specific order of visiting.  Modifying
    dirnames when topdown is false is ineffective, since the directories in
    dirnames have already been generated by the time dirnames itself is
    generated.

    By default errors from the os.listdir() call are ignored.  If
    optional arg 'onerror' is specified, it should be a function; it
    will be called with one argument, an os.error instance.  It can
    report the error to continue with the walk, or raise the exception
    to abort the walk.  Note that the filename is available as the
    filename attribute of the exception object.

    By default, os.walk does not follow symbolic links to subdirectories on
    systems that support them.  In order to get this functionality, set the
    optional argument 'followlinks' to true.

    Caution:  if you pass a relative pathname for top, don't change the
    current working directory between resumptions of walk.  walk never
    changes the current directory, and assumes that the client doesn't
    either.

    Example:

    from os.path import join, getsize
    for root, dirs, files in walk('python/Lib/email'):
        print root, "consumes",
        print sum([getsize(join(root, name)) for name in files]),
        print "bytes in", len(files), "non-directory files"
        if 'CVS' in dirs:
            dirs.remove('CVS')  # don't visit CVS directories
    """

    from os.path import join, isdir, islink

    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.path.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        # Note that listdir and error are globals in this module due
        # to earlier import-*.
        names = os.listdir(top)
    except os.error, err:
        if onerror is not None:
            onerror(err)
        return

    dirs, nondirs = [], []
    for name in names:
        if isdir(join(top, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    if topdown:
        yield top, dirs, nondirs
    for name in dirs:
        path = join(top, name)
        if followlinks or not islink(path):
            for x in walk(path, topdown, onerror, followlinks):
                yield x
    if not topdown:
        yield top, dirs, nondirs

def maybeInt(s):
    if s.isdigit():
        return int(s)
    return s

def naturalSort(l):
    l.sort(key = lambda d: map(maybeInt, d.split("-")))

class Experiment(object):
    def __init__(self, path):
        self.__path = path
        self.__info = None

    def __repr__(self):
        return "Experiment(%r)" % self.__path

    @property
    def path(self):
        return self.__path

    @property
    def info(self):
        if self.__info == None:
            # Old style
            p = os.path.join(self.__path, "config")
            if not os.path.exists(p):
                # New style
                p = os.path.join(self.__path, "info")
            self.__info = pickle.load(file(p))
        return self.__info

    def openLog(self, cfgDict):
        return file(os.path.join(self.__path, "log", cfgDict["name"]))

def experiments(*dirs):
    """Generate a sequence of Experiment's under dirs, sorted in a
    reasonable way."""

    for d in dirs:
        for (dirpath, dirnames, filenames) in walk(d, followlinks=True):
            if "info" in filenames or "config" in filenames:
                dirnames[:] = []
                yield Experiment(dirpath)
            else:
                naturalSort(dirnames)

def series(*dirs):
    """Find all experiment series under dirs.  Generates a sequence of
    (name, [Experiment]) pairs for each series where name is some
    reasonable path-based identifier and [Experiment] is a list of
    Experiment's in this series."""

    # Find each series under all directories in dirs.  Keep them in
    # some reasonable order.
    pdirMap = {}                # series dir -> [point dir]
    order = []
    for top in dirs:
        for (dirpath, dirnames, filenames) in walk(top, followlinks=True):
            if "info" in filenames or "config" in filenames:
                dirnames[:] = []
                # dirpath contains the data point and its parent
                # contains the series
                sdir = os.path.dirname(dirpath) + "/"
                if sdir not in pdirMap:
                    pdirMap[sdir] = []
                    order.append(sdir)
                pdirMap[sdir].append(os.path.abspath(dirpath))
            else:
                naturalSort(dirnames)

    # Get the common prefix of the series directories
    common = os.path.commonprefix(order)
    if not common.endswith("/"):
        # commonprefix works character-by-character and we got part of
        # a path.  Trim off the partial match.
        common = os.path.dirname(common) + "/"

    # Yield each series
    for sdir in order:
        yield sdir[len(common):].rstrip("/"), map(Experiment, pdirMap[sdir])

def filterInfo(info, **selectors):
    """Filter the information list, returning only the information
    dictionaries that match all of the items in selectors.  The
    'className' selector is treated specially to deal with subclassing
    relations."""

    className = selectors.pop("className", None)
    print 'KESL' + className

    for dct in info:
        if className != None:
            if "classNames" in dct:
                if className not in dct["classNames"]:
                    continue
            else:
                raise ValueError("No class name for %r" % dct)
        for k, v in selectors.iteritems():
            if k not in dct or dct[k] != v:
                break
        else:
            yield dct

def the(it):
    """If the given iterator produces just one unique value, return
    it.  Otherwise, raise ValueError."""

    first = True
    out = None
    for v in it:
        if first:
            out = v
            first = False
        else:
            if out != v:
                raise ValueError("More than one value")
    if first:
        raise ValueError("Empty sequence")
    return out
