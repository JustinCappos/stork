#! /usr/bin/env python
"""
   Created by Mario Gonzalez. Improved by Jeffry Johnston.
   
   Usage examples:
       Run all tests:
           ./storktests.py
       Run only the tests in arizonageneralTest.py:
           ./storktests.py arizonageneralTest
"""

import sys
import os
import unittest
import arizonaconfig

# find the directory that this script is in and add its "test" subdirectory to the path
program = sys.argv[0]
abspath = os.path.realpath(program)
if program != "":
   abspath = os.path.split(abspath)[0]
os.environ["TESTPREFIX"] = abspath
sys.path.append(abspath+"/test")
testpath = abspath + "/test"
print "Using tests in directory: "+testpath 

# if there is an argument that was passed, it is a request to only one run test module
if len(sys.argv) == 2:
    onlyrunmodule = sys.argv[1]
else:
    onlyrunmodule = None

# define test modules to ignore
# (e.g. they won't compile so this script exit before any tests are run)
ignoretests = []
#ignoretests.append('arizonacommTest')
#ignoretests.append('arizonatransfer_coblitzTest')
#ignoretests.append('arizonatransfer_coralTest')
#ignoretests.append('arizonatransfer_ftpTest')
#ignoretests.append('arizonatransfer_httpTest')
#ignoretests.append('planetlab_shareTest')
#ignoretests.append('stork_nest_commTest')
#ignoretests.append('stork_nestrpm_prepare_packageTest')
#ignoretests.append('storkidentifyTest')
#ignoretests.append('storkrpmTest')
#ignoretests.append('storktargzTest')
#ignoretests.append('storkrpmTest')

# get a list of the existing tests
testsuites = []
for file in os.listdir(testpath):
   if os.path.isfile(testpath + "/" + file):
       if file[-7:] == 'Test.py':
           modulename = file[:-3]
           if onlyrunmodule is not None and modulename != onlyrunmodule:
               continue
           elif modulename in ignoretests:
               continue
           testmodule = __import__(modulename)
           testsuites.append(unittest.TestLoader().loadTestsFromTestCase(testmodule.test))

# initialize config values, as this seems to be only done at the moment
# in the if __name__ == '__main__': section of the test files.
arizonaconfig.init_options()

# run the tests
alltests = unittest.TestSuite(testsuites)
unittest.TextTestRunner(verbosity=3).run(alltests)

# old system of running single tests below.
# left here for the sake of example, should it be useful
#-------------------------------------------------------
# test-specific commands start here:
#------------------------------------------------------

#import storkTest
#import storkpackageTest
#import storktrustedpackagesparseTest
#import arizonageneralTest
#import arizonaconfigTest
#import storkpackagelistTest
#import storkextractmetaTest
#import storkidentifyTest
#import arizonacryptTest

#t = storkpackageTest
#t = storktrustedpackagesparseTest
#t = storkidentifyTest
#t = storkextractmetaTest
#t = arizonaconfigTest
#t = storkpackagelistTest
#t = arizonacryptTest

#suite = unittest.makeSuite(t.test)
#unittest.TextTestRunner(verbosity=3).run(suite)

#----------------------- test-specific commands end here----------

print "Done"
