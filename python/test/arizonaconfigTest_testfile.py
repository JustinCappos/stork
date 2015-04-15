#! /usr/bin/env python
"""
<Purpose>
   This is a test file to be read in by arizonaconfigTest
"""

#           [option, long option,     variable,      action,        data,     default,                           metavar,     description]
"""arizonaconfig
   options=[
            ["-C",   "--configfile",  "configfile",  "store",       "string", "arizonaconfigTest.conf", "FILE",      "use a different config file (arizonaconfigTest.conf is the default)"],
            ["",     "--listenport",  "listenport",  "store",       "int",    648,                               "PORT",      "bind to this port (default 648)"],
            ["",     "--bindfiles",   "bindfiles",   "store",       "string", "/share/base",                     "DIRECTORY", "location of the files to copy to the client upon binding"],
            ["",     "--retrievedir", "retrievedir", "store",       "string", "/usr/local/stork/var/packages",   "DIRECTORY", "location to put retrieved files (default /usr/local/stork/var/packages)"],
            ["",     "--not-daemon",  "daemon",      "store_false",  None,    True,                              None,        "specify that program should not attempt to detach from the terminal"],
            ["",     "--localoutput", "localoutput", "store_true",   None,    False,                             None,        "display output locally, do not send to client"],

            ["",     "--include",     "include",     "append",       "string", None,                               None,        "include config file"],

            ["",     "--sliceport",  "sliceport",  "store",       "string",    "640",                               "PORT",      "unknown (default 640)"]]


   includes=[]
"""

# NOTE: technically the following is incorrect and it should be only
# arizonaconfigTest_testfile2, but arizonaconfig is looking in the wrong
# directory.
# TODO: Investigate.
import test.arizonaconfigTest_testfile2
# this one has new tests
import test.arizonaconfigTest_testfile4

