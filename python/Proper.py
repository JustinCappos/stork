#!/usr/bin/python

import fcntl
import getopt
import os
import re
import select
import sys
import time
import urllib



# default port number
HTTP_PORT = 6502

# file flags
FILE_FLAGS = { "nochange": 1, "nounlink": 2 }

# prefix used by mount/unmount to specify a slice domain
SLICE_PREFIX_RE = re.compile(r"^[a-z0-9]+_[a-z0-9_]+:/")



class Worker:

    def __init__(self, port = HTTP_PORT, debug = False, timeout = None):

        self.port = port
        self.debug = debug
        self.timeout = timeout

    def __buildurl(self, op, args):

        def argpairs((outlist, index), arg):
            return (outlist + [("arg%d" % index, arg)], index + 1)

        (argpairs, argcount) = reduce(argpairs, args, ([], 0))
        argstr = urllib.urlencode(argpairs)

        return "http://localhost:%u/%s?%s" % (self.port, op, argstr)

    def __execop(self, op, args):

        url = self.__buildurl(op, args)
        if self.debug:
            print >>sys.stderr, "GET " + url
        urlconn = urllib.urlopen(url)
        output = ""
        if self.timeout:
            poller = select.poll()
            poller.register(urlconn, select.POLLIN)
            fcntl.fcntl(urlconn, fcntl.F_SETFL, os.O_NONBLOCK)
            begin = time.time()
            now = begin
        while True:
            if self.timeout:
                delay = self.timeout - int((now - begin) * 1000)
                if self.debug:
                    print >>sys.stderr, "delay = %dms" % delay
                if delay <=0 or not poller.poll(delay):
                    raise IOError, "timed-out"
                now = time.time()
            try:
                data = urlconn.read()
            except socket.error:
                # XXX - sometimes we get back EAGAIN from read()
                continue
            if not data:
                break
            output += data
        urlconn.close()

        return output

    def __getattr__(self, method):

        return lambda *args: self.__execop(method, args)



def get_file_flags(file):

    return Worker().get_file_flags(file)

def set_file_flags(file, flags):

    return Worker().set_file_flags(file, flags)

def mount_dir(source, mntpoint, options = None, worker = Worker()):

    # check whether arguments are reversed to indicate an implicit 'putdir'
    if SLICE_PREFIX_RE.match(mntpoint) and not SLICE_PREFIX_RE.match(source):
        if worker.debug:
            print >>sys.stderr, "assuming implicit putdir"
        if options:
            assert options.find("putdir") == -1
            options += ",putdir"
        else:
            options = "putdir"
        (source, mntpoint) = (mntpoint, source)

    args = (source, mntpoint)
    if options:
        args += (options, )

    return worker.mount_dir(*args)

def unmount(mntpoint, worker = Worker()):

    # XXX - workaround until server fixed
    if SLICE_PREFIX_RE.match(mntpoint):
        mntpoint = "/vservers/" + mntpoint

    return Worker().unmount(mntpoint)

def parse_file_flags(argv):

    flags = 0
    if argv[0] == "0":
        del argv[0]
    else:
        while argv:
            if argv[0][0] == '-':
                flags &= ~FILE_FLAGS[argv[0][1:]]
            elif argv[0][0] == '+':
                flags |= FILE_FLAGS[argv[0][1:]]
            else:
                break
            del argv[0]
    if not argv:
        raise Exception, "no files specified"

    return (flags, argv)

def usage():

    print "usage:\n" \
          "    prop <command>\n" \
          "\n" \
          "where <command> is\n" \
          "    getflags <filename>\n" \
          "    setflags <flags> <filename>+\n" \
          "    mountdir <domain> <dir> <mntpoint> [<options>]\n" \
          "    unmount  <mntpoint>\n"
    sys.exit(1)



def main(argv):

    debug = False
    port = HTTP_PORT
    timeout = None
    verbose = False

    if len(argv) < 2:
        usage()

    (opts, argv) = getopt.getopt(argv, "dp:t:v")
    for (opt, optval) in opts:
        if opt == "-d":
            debug = True
        elif opt == "-p":
            port = int(optval)
        elif opt == "-t":
            try:
                timeout = int(optval)
            except ValueError:
                timeout = int(float(optval) * 1000)
        elif opt == "-v":
            verbose = True

    worker = Worker(port, debug, timeout)

    def filter_output(output, prefix = ""):
        output = output.strip()
        if debug:
            print >>sys.stderr, output
        ok = re.match(r"^OK: ([0-9A-Fa-f]+)$", output)
        if ok:
            result = int(ok.expand(r"\1"), 16)
            if result or verbose:
                output = str(result)
            else:
                return
        print prefix + output

    if argv[0] == "getflags":
        op = worker.get_file_flags
    elif argv[0] == "setflags":
        if argv[1][0] == '-' or argv[1][0] == '+' or argv[1] =="0":
            (flags, argv[1:]) = parse_file_flags(argv[1:])
            def do_one_file(f):
                output = worker.set_file_flags(f, flags)
                filter_output(output, f + ": ")
            op = lambda *files: (map(do_one_file, files), None)[1]
        else:
            assert len(argv[1:]) == 2
            op = worker.set_file_flags
    elif argv[0] == "mountdir":
        op = lambda *args: mount_dir(worker = worker, *args)
    elif argv[0] == "unmount":
        op = lambda *args: unmount(worker = worker, *args)
    else:
        print >>sys.stderr, "Invalid command: %s" % argv[0]
        usage()

    try:
        output = op(*argv[1:])
    except IOError, ex:
        print >>sys.stderr, "IOError: " + str(ex)
        sys.exit(1)

    if output:
        filter_output(output)



if __name__ == "__main__":
    main(sys.argv[1:])
