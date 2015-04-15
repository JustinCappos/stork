#! /usr/bin/env python
"""
<Module>
   storkpackageTest
<Author>
   Justin Cappos

   Extended by Mario Gonzalez
   
<Started>
   May 23, 2006
<Purpose>
   Test module for storkpackage.  See storkpackage.py for more details.
"""

import os
import arizonaconfig
import arizonatransfer
import arizonaunittest
import storkpackagelist
import arizonageneral
import storkpackage
import sys
from package import storktar

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):


   #------------------------------------------------------------------
   # reset_options(): call this every time you wish to set or re-set the options
   # since the tests are not called in order
   #------------------------------------------------------------------
   def reset_options(self):
      self.set_cmdline([])
      prefix = os.environ.get("TESTPREFIX")
      storkpackage.reset()
      arizonaconfig.init_options("storkpackage.py", alt_paths=[prefix], version="2.0")
                  
   
   #------------------------------------------------------------------
   # init():
   #------------------------------------------------------------------
   def test_initialize(self):

      # set or re-set the options since the tests are not called in order
      self.reset_options()

      # no "packagemanagers" should exist yet
      arizonaconfig.reset()
      
      # should raise an exception if arizonaconfig.init_options() has not been called yet or
      # no option has been set:
      self.assertException(Exception, storkpackage.initialize) 
      self.assertException(Exception, storkpackage.initialize, None) 
      # check that a specific exception is raised (white box test):
      self.assertRaises(arizonageneral.Exception_Data, storkpackage.initialize)

      # assert that the expected message is the actual one
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: missing --packagemanagers setting", storkpackage.initialize)

      # White box: do preparation so that arizonaconfig.init_options()
      # has been successfuly called prior to running storkpackage.initialize()
      # since this is needed by storkpackage.initialize():

      # ---- TEST STARTS ------------------------------------------------------------------------------
      # Prepare the options to test storkpackage: make sure init_options 
      # run successfully but storkpackage.initialize() does NOT find any
      # usable package managers

      # set or re-set the options since the tests are not called in order
      self.reset_options()
      self.set_cmdline([])

      # create new option (which is invalid.. string instead of list of strings)
      arizonaconfig.set_option("packagemanagers", "rpm")
      self.assertEqual(arizonaconfig.get_option("packagemanagers"), "rpm")

      # Now that the options have been successfuly initialized, 
      # test the method:
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.initialize)
      self.assertTrue(storkpackage.possible_packmanagers != None)
      self.assertEquals(len(storkpackage.inited_packmanager_list), 0)
      self.assertTrue(storkpackage.glo_packagemanagers_provide == [])

      # create new option
      self.reset_options()
      arizonaconfig.set_option("packagemanagers", "an unusable package manager")
      self.assertEqual(arizonaconfig.get_option("packagemanagers"), "an unusable package manager")

      # Now that the options have been successfuly initialized,
      # test the method:
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.initialize)
      self.assertTrue(storkpackage.possible_packmanagers != None)
      self.assertEquals(len(storkpackage.inited_packmanager_list), 0)
      self.assertTrue(storkpackage.glo_packagemanagers_provide == [])
                                                                                                
      # ---- TEST ENDS ------------------------------------------------------------------------------      

      # ---- TEST STARTS ------------------------------------------------------------------------------
      # Prepare the options to test storkpackage: make sure init_options 
      # run successfully and storkpackage.initialize() DOES find 
      # usable package managers
      self.reset_options()

      # Is this actually needed or should init_options see and set "packagemanagers" itself?
      #arizonaconfig.set_option("packagemanagers", ["rpm", 'tar'])
      self.assertEquals(["rpm", "tar"], arizonaconfig.get_option("packagemanagers"))

      # Now that arizonaconfig.init_options() has been successfuly called, 
      # test the method:
      try:
          storkpackage.initialize()
      except arizonageneral.Exception_Data:
          self.fail("Should not have failed")
      self.assertTrue(storkpackage.possible_packmanagers != None)
      self.assertTrue(len(storkpackage.inited_packmanager_list) > 0)
      # the following line is simply to output the contents of inited_packmanager_list. Comment out when not
      # needed. Note that it IS NOT A TEST!
      #self.assertEquals("", storkpackage.inited_packmanager_list)
      self.assertEquals("/usr/local/stork/tar_packinfo", arizonaconfig.get_option('tarpackinfopath'))
      self.assertTrue(len(storkpackage.glo_packagemanagers_provide) > 0 )
      self.assertTrue(storkpackage.glo_packagemanagers_provide != None)
      self.assertTrue(storkpackage.glo_packagemanagers_provide != [])
      # ---- TEST ENDS ------------------------------------------------------------------------------


      # ---- TEST STARTS ------------------------------------------------------------------------------
      # Call initialize but set the package manager options like this: ['tar', 'rpm']. That is, first
      # tar and then rpm.
      self.reset_options()
      #arizonaconfig.set_option("packagemanagers", ['tar', 'rpm'])
      #self.assertEquals(["tar", "rpm"], arizonaconfig.get_option("packagemanagers"))

      # Now that arizonaconfig.init_options() has been successfuly called,
      # test the method:
      try:
         storkpackage.initialize()
      except arizonageneral.Exception_Data:
         self.fail("Should not have failed")
      self.assertTrue(storkpackage.possible_packmanagers != None)
      self.assertTrue(len(storkpackage.inited_packmanager_list) > 0)
      # The following line is simply to output the contents of inited_packmanager_list. Comment out when not
      # needed. Note that it IS NOT A TEST!
      #self.assertEquals("", storkpackage.inited_packmanager_list)
      self.assertEquals("/usr/local/stork/tar_packinfo", arizonaconfig.get_option('tarpackinfopath'))
      self.assertTrue(len(storkpackage.glo_packagemanagers_provide) > 0 )
      self.assertTrue(storkpackage.glo_packagemanagers_provide != None)
      self.assertTrue(storkpackage.glo_packagemanagers_provide != [])
                                                                                            
      # ---- TEST ENDS ------------------------------------------------------------------------------
      
      
      
   #------------------------------------------------------------------
   # get_packagemanagers_provide()
   #------------------------------------------------------------------
   def test_get_packagemanagers_provide(self):
      self.reset_options()
      arizonaconfig.reset()
      
      # should raise an exception if arizonaconfig.init_options() has not been called yet:
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: missing --packagemanagers setting", storkpackage.initialize)
      self.assertException(Exception, storkpackage.get_packagemanagers_provide)
      # check that a specific exception is raised (white box test):
      self.assertRaises(arizonageneral.Exception_Data, storkpackage.get_packagemanagers_provide)


      # White box: do preparation so that some needed options are initialized 
      # prior to running this method

      # ---- TEST STARTS ------------------------------------------------------------------------------
      # The tests are the same as for initialize() since initialize() is the only method called.
      # ---- TEST ENDS ------------------------------------------------------------------------------


   #------------------------------------------------------------------
   # is_package_understood():
   #------------------------------------------------------------------
   def test_is_package_understood(self):
      reload(storkpackage)
      self.reset_options()

      prefix = os.environ.get("TESTPREFIX")
      
      # test with invalud input:
      self.assertRaises(TypeError, storkpackage.is_package_understood, None)
      self.assertRaises(TypeError, storkpackage.is_package_understood, [])
      self.assertRaises(TypeError, storkpackage.is_package_understood, ["sdsd"])
      self.assertRaises(TypeError, storkpackage.is_package_understood, 23)
      self.assertRaises(TypeError, storkpackage.is_package_understood, 56.3)

      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: missing --packagemanagers setting", storkpackage.is_package_understood, 'filename')
      
      self.assertException(Exception, storkpackage.is_package_understood)

      # White box: do preparation so that some needed options are initialized 
      # prior to running this method

      # ---- TEST STARTS ------------------------------------------------------------------------------
      # Prepare the options to test storkpackage: make sure init_options 
      # run successfully but storkpackage.initialize() does NOT find any
      # package managers that can be UNDERSTOOD:
      
      # set or re-set the options since the tests are not called in order
      self.reset_options()

      # create new option
      arizonaconfig.set_option("packagemanagers", "an invalid package manager")
      self.assertEqual(arizonaconfig.get_option("packagemanagers"), "an invalid package manager")

      # Now that arizonaconfig.init_options() has been successfuly called, 
      # test the method. Note that is should raise exceptions since there are no valid package managers:
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.is_package_understood, "")
 
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.is_package_understood, ".")

      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.is_package_understood, "''")
            
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.is_package_understood, "rpm")

      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.is_package_understood, "some invalid package")
      

      # ---- TEST ENDS ------------------------------------------------------------------------------


      # Make the following tests independent of the testing path:
      # Extract the path where "stork/..." starts and leave the part before this substring to a variable
      # that will change so that the tests can be run in different machines:
      subIdx = prefix.find("stork")
      path = prefix[:subIdx]
      #self.debug_print(path)

                              
      # ---- TEST STARTS ------------------------------------------------------------------------------
      # Prepare the options to test storkpackage: make sure init_options 
      # run successfully and  storkpackage.initialize() DOES find 
      # package managers that can be UNDERSTOOD:

      # Test with tar package manager
      self.reset_options()

      arizonaconfig.set_option("packagemanagers", ["tar"])
      # Now that arizonaconfig.init_options() has been successfuly called, 
      # test the method:
      self.assertFalse(storkpackage.is_package_understood("some invalid file name here"))
      self.assertFalse( storkpackage.is_package_understood( "hello"))
      self.assertFalse( storkpackage.is_package_understood( ""))
      self.assertFalse( storkpackage.is_package_understood( " "))
      self.assertFalse( storkpackage.is_package_understood( "-*"))
      # the following two lines freeze up is_package_understood()
      #self.assertFalse( storkpackage.is_package_understood( "-"))
      #self.assertFalse( storkpackage.is_package_understood( "- "))
      self.assertFalse( storkpackage.is_package_understood("- dashSpaceAndSomeName"))
      self.debug_print("hi")
      self.assertFalse( storkpackage.is_package_understood( "."))
      self.assertFalse( storkpackage.is_package_understood( "storktar.pyc"))
      self.assertFalse( storkpackage.is_package_understood( " some string "))
      self.assertFalse( storkpackage.is_package_understood( prefix + "/package/storktar.pyc"))
      # test with valid package filenames
      
      self.assertTrue(storkpackage.is_package_understood(path + "stork/webpage/downloads/stork_example.tar.gz"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/webpage/downloads/stork_key.tar.gz"))

      # exists but contains ???
      #self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/stork-0.1.0.tar"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0.tar.gz"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1.tar.gz"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.2.tar.gz"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-0.1.tar.gz"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-10.1.tar.gz"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-9.1.tar.gz"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/python/tests/install.tar.gz"))
      
      self.assertTrue(storkpackage.is_package_understood(path + "stork/python/refactor/package-dir.tar"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/python/package-dir/lib-package/arizona-lib-1.0.0.tar.gz"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/keypack/stork_key.tar.gz"))

      # does not exist
      #self.assertTrue(storkpackage.is_package_understood(path + "stork/2.0/stork.tar.bz2"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/repository.tar.gz"))

      # "rpm" is not set as a manager, so these calls must return false:
      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/stork-0.1.0-1.i386.rpm"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/stork-0.1.0-1.src.rpm"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0-1.i386.rpm"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0-1.src.rpm"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1-1.i386.rpm"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1-1.src.rpm"))
                                    


      # Now test with rpm package manager
      self.reset_options()
      arizonaconfig.set_option("packagemanagers", ["rpm"])
      self.assertEqual(['rpm'], arizonaconfig.get_option("packagemanagers"))
      storkpackage.initialize()
      self.debug_print(storkpackage.inited_packmanager_list)
      for i in storkpackage.inited_packmanager_list:
         self.debug_print(i[1])
      # Now that arizonaconfig.init_options() has been successfuly called,
      # test the method:
      self.assertFalse( storkpackage.is_package_understood( " "))
      self.assertFalse( storkpackage.is_package_understood( "some invalid file name here" ))
      self.assertFalse(storkpackage.is_package_understood("filename"))
      self.assertFalse( storkpackage.is_package_understood( "-"))
      self.assertFalse( storkpackage.is_package_understood("- dashSpaceAndSomeName"))
      self.assertFalse( storkpackage.is_package_understood("- "))
      self.assertFalse( storkpackage.is_package_understood( "."))
      self.assertFalse( storkpackage.is_package_understood( "2322"))
      self.assertFalse( storkpackage.is_package_understood(""))
      #self.assertFalse( storkpackage.is_package_understood( prefix + "/package/storkrpm.pyc"))
      # test with valid package filenames
      # Since the valid packages are stored in the stork/ directory, take the last part off of the
      # prefix so that the packages can be accessed by the tests:
      #testStringIdx = prefix.find("stork/2.0/python")
      #pathString = prefix.ljust(testStringIdx, None)
      #self.assertEquals(None, pathString)

#      # Make the following tests independent of the testing path:
#      # Extract the path where "stork/..." starts and leave the part before this substring to a variable
#      # that will change so that the tests can be run in different machines:
#      subIdx = prefix.find("stork")
#      path = prefix[:subIdx]
#      #self.debug_print(path)

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/stork-0.1.0-1.i386.rpm"))
   
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/stork-0.1.0-1.src.rpm"))
      
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0-1.i386.rpm"))
      
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0-1.src.rpm"))
      
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1-1.i386.rpm"))
      
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1-1.src.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.2-1.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.2-1.src.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-0.1-1.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-0.1-1.src.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-9.1-1.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-9.1-1.src.rpm"))

      # exists but is empty:
      #self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testc-0.1-1.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/python/tests/cpio-2.5-6.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/python/tests/stork-1.0.0-1.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/python/tests/stork-slice-1.0.0b-3.i386.rpm"))

      # does not exist anymore
      #self.assertTrue(storkpackage.is_package_understood(path + "stork/pack/stork-slice-1.0.0-1.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/pack/cpio-2.5-6.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/appman/remote/do_install/cpio-2.5-6.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/appman/remote/do_install/stork-slice-1.0.0b-3.i386.rpm"))
      
      self.assertTrue(storkpackage.is_package_understood(path + "stork/appman/remote/inst/authd-0.2.2-1.i386.rh9.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/appman/remote/inst/pcp-0.3.3-1.i386.rh9.rpm"))
      
      self.assertTrue(storkpackage.is_package_understood(path + "stork/appman/remote/inst/tcp_wrappers-7.6-36.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/appman/remote/inst/xinetd-2.3.13-2.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/pyspecer/stork/BitTorrent-4.0.4-1.noarch.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/pyspecer/stork/PyXML-0.8.3-6.i386.rpm"))

      self.assertTrue(storkpackage.is_package_understood(path + "stork/pyspecer/stork/cpio-2.5-6.i386.rpm"))

      self.debug_print("passed rpm packages")
      
      # "tar" is not set as a package manager, so the calls should return false:
      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0.tar.gz"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1.tar.gz"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/testa-0.2.tar.gz"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/testb-0.1.tar.gz"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/testb-10.1.tar.gz"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/testpack/testb-9.1.tar.gz"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/python/tests/install.tar.gz"))

      self.assertFalse(storkpackage.is_package_understood(path + "stork/python/refactor/package-dir.tar"))

      self.debug_print("passed tar")
      
      
      # test with both rpm and tar as package managers
      self.reset_options()
      arizonaconfig.set_option("packagemanagers", ["rpm", "tar"])
      self.assertFalse( storkpackage.is_package_understood(" "))
      self.assertFalse( storkpackage.is_package_understood('some invalid file name here'))
      self.assertFalse( storkpackage.is_package_understood("filename "))
      
      self.assertFalse( storkpackage.is_package_understood( "-*"))
      # the following two lines freeze up is_package_understood()
      #self.assertFalse( storkpackage.is_package_understood( "-"))
      #self.assertFalse( storkpackage.is_package_understood( "- "))
      self.assertFalse( storkpackage.is_package_understood("- dashSpaceAndSomeName"))         
      self.assertFalse( storkpackage.is_package_understood("123"))
      self.assertFalse( storkpackage.is_package_understood(prefix + "/package/storkrpm.pyc"))
      self.assertFalse( storkpackage.is_package_understood(prefix + "/package/storktar.pyc"))
      # now test with valid filenames
      self.debug_print("passed invalid filenames")
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0.tar.gz"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1.tar.gz"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.2.tar.gz"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-0.1.tar.gz"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-10.1.tar.gz"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-9.1.tar.gz"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/python/tests/install.tar.gz"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/python/refactor/package-dir.tar"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/stork-0.1.0-1.i386.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/stork-0.1.0-1.src.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0-1.i386.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/storkd-0.1.0-1.src.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1-1.i386.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.1-1.src.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.2-1.i386.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testa-0.2-1.src.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-0.1-1.i386.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-0.1-1.src.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-9.1-1.i386.rpm"))
      self.assertTrue(storkpackage.is_package_understood(path + "stork/testpack/testb-9.1-1.src.rpm"))
                                                                        
      
      # ---- TEST ENDS ------------------------------------------------------------------------------



   #------------------------------------------------------------------
   # get_package_metadata():
   #------------------------------------------------------------------
   def test_get_package_metadata(self): #(filename):
      arizonaconfig.reset()
      storkpackage.reset()

      # pass invalid parameter
      self.assertException(TypeError, storkpackage.get_package_metadata, [])
      self.assertException(TypeError, storkpackage.get_package_metadata, {})
      self.assertException(TypeError, storkpackage.get_package_metadata, ())
      self.assertException(TypeError, storkpackage.get_package_metadata, 23)
      self.assertException(TypeError, storkpackage.get_package_metadata, 34.5)
      self.assertException(TypeError, storkpackage.get_package_metadata, ["asa"])

      self.reset_options()

      prefix = os.environ.get("TESTPREFIX")
      # Make the following tests independent of the testing path:
      # Extract the path where "stork/..." starts and leave the part before this substring to a variable
      # that will change so that the tests can be run in different machines:
      subIdx = prefix.find("stork")
      path = prefix[:subIdx]
      #self.debug_print(path)


      #-------------------- SUBTEST STARTS --------------------------------------------------------
      # Right now, test with rpm packages only:
      arizonaconfig.set_option("packagemanagers", ['rpm'])
      
      # Make it raise TypeError with "unrecognized package format" message:
      # Pass it a name of a file that does NOT exist:
      self.assertException(TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/file-9.1-1.src.rpm")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, "some unknown file")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, "- some unknownfile")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, "- ")
      # Pass it an existing rpm file that is EMPTY:
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, path + "stork/testpack/testc-0.1-1.i386.rpm")
      # Pass 'tar' packages
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, path + "stork/testpack/storkd-0.1.0.tar.gz")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, path + "stork/testpack/testa-0.1.tar.gz")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, path + "stork/testpack/testa-0.2.tar.gz")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, path + "stork/testpack/testb-10.1.tar.gz")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, path + "stork/python/tests/install.tar.gz")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, path + "stork/python/refactor/package-dir.tar")
      
      
      # TODO: Make it raise IOError:
      # Do not open the file with "w" because this will erase its contents.
      #f = file(path + "stork/testpack/testa-0.2-1.i386.rpm", "r")
      #self.assertException(IOError, storkpackage.get_package_metadata, path + "stork/testpack/testa-0.2-1.i386.rpm")
      #f.close()


      # Pass valid 'rpm' package names
      #self.debug_print(  storkpackage.get_package_metadata( path + "stork/testpack/testa-0.2-1.i386.rpm" ) )
      # The dictionary returned must contain 9 key-value pairs with the following keys: 'filename', 'name',
      # 'version', 'release', 'size', 'hash', 'provides', 'requires', 'files'.
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testa-0.2-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/stork-0.1.0-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/storkd-0.1.0-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/storkd-0.1.0-1.src.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testa-0.2-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testb-0.1-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testb-9.1-1.src.rpm" ) ) )
      
      #-------------------- SUBTEST ENDS --------------------------------------------------------
      

      #-------------------- SUBTEST STARTS --------------------------------------------------------
      # Now, test with 'tar' packages only:
      arizonaconfig.reset()
      self.reset_options()
      arizonaconfig.set_option("packagemanagers", ['tar'])
      self.assertEqual(arizonaconfig.get_option("packagemanagers"), ['tar'])
      
      # Make it raise TypeError with "unrecognized package format" message:
      # Pass it a name of a file that does NOT exist:
      self.assertException(TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/file-9.1-1.src.tar")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, "some unknownfile")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, "- some unknownfile")
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, "- ")
      # Pass it an existing tar file that is EMPTY:
      f = file(path + "stork/testpack/testc-0.1-1.i386.tar", 'w')
      f.close()
      self.assertExceptionMessage(TypeError, "Unrecognized package format",  storkpackage.get_package_metadata, path + "stork/testpack/testc-0.1-1.i386.tar")
      os.remove(path + "stork/testpack/testc-0.1-1.i386.tar")
      # make sure that the file was erased by this test
      self.assertException(IOError, file, path + "stork/testpack/testc-0.1-1.i386.tar", "r")
            
      # Pass it 'rpm' packages
      self.assertExceptionMessage( TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/testa-0.2-1.i386.rpm" )
      self.assertExceptionMessage( TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/stork-0.1.0-1.i386.rpm" )
      self.assertExceptionMessage( TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/storkd-0.1.0-1.i386.rpm"  )
      self.assertExceptionMessage( TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/storkd-0.1.0-1.src.rpm" )
      self.assertExceptionMessage( TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/testa-0.2-1.i386.rpm" ) 
      self.assertExceptionMessage( TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/testb-0.1-1.i386.rpm" ) 
      self.assertExceptionMessage( TypeError, "Unrecognized package format", storkpackage.get_package_metadata, path + "stork/testpack/testb-9.1-1.src.rpm" ) 
                                          
      # Pass valid 'tar' package names
      # The dictionary returned must contain 9 key-value pairs with the following keys: 'filename', 'name',
      # 'version', 'release', 'size', 'hash', 'provides', 'requires', 'files'.
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/storkd-0.1.0.tar.gz" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testa-0.1.tar.gz") ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testa-0.2.tar.gz") ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testb-10.1.tar.gz") ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/python/tests/install.tar.gz") ) )      
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/python/refactor/package-dir.tar") ) )
                                                                  
      #-------------------- SUBTEST ENDS --------------------------------------------------------


      #-------------------- SUBTEST STARTS --------------------------------------------------------
      # Now, test with both tar and rpm packages:
      arizonaconfig.reset()
      self.reset_options()
      self.assertEqual(arizonaconfig.get_option("packagemanagers"), ['rpm', 'tar'])
                        
      # Pass valid 'tar' and 'rpm' package names
      # The dictionary returned must contain 9 key-value pairs with the following keys: 'filename', 'name',
      # 'version', 'release', 'size', 'hash', 'provides', 'requires', 'files'.
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/storkd-0.1.0.tar.gz" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testa-0.1.tar.gz") ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testa-0.2.tar.gz") ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testb-10.1.tar.gz") ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/python/tests/install.tar.gz") ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/python/refactor/package-dir.tar") ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testa-0.2-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/stork-0.1.0-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/storkd-0.1.0-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/storkd-0.1.0-1.src.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testa-0.2-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testb-0.1-1.i386.rpm" ) ) )
      self.assertEqual( 9, len( storkpackage.get_package_metadata( path + "stork/testpack/testb-9.1-1.src.rpm" ) ) )
                                          
      #-------------------- SUBTEST ENDS --------------------------------------------------------
      


   #------------------------------------------------------------------
   # get_packages_provide():
   #------------------------------------------------------------------
   def test_get_packages_provide(self):
      self.reset_options()

      self.assertException(TypeError, storkpackage.get_packages_provide, "filename")
      self.assertException(TypeError, storkpackage.get_packages_provide, "")
      self.assertException(TypeError, storkpackage.get_packages_provide, {})
      self.assertException(TypeError, storkpackage.get_packages_provide, ())
      self.assertException(TypeError, storkpackage.get_packages_provide, 23)

      # set arizonaconfig to its initial state so that "packagemanagers" options is not set.
      #self.reset_options()
      arizonaconfig.reset()
      #storkpackage.reset()
      self.assertEqual([], storkpackage.get_packages_provide([]))
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: missing --packagemanagers setting", storkpackage.get_packages_provide, ['filename'])


      # Make the following tests independent of the testing path:
      # Extract the path where "stork/..." starts and leave the part before this substring to a variable
      # that will change so that the tests can be run in different machines:
      prefix = os.environ.get("TESTPREFIX")
      subIdx = prefix.find("stork")
      path = prefix[:subIdx]
      #self.debug_print(path)

                                    
      # Set the options so that initialize() does not throw an exception
      self.reset_options()
      self.assertEqual([], storkpackage.get_packages_provide(["filename"]))
      self.assertEqual([], storkpackage.get_packages_provide([]))
      # subtests with valid rpm and tar packages
      self.debug_print(storkpackage.get_packages_provide([path + "stork/testpack/testb-9.1-1.src.rpm"]))
      self.debug_print(storkpackage.get_packages_provide([path + "stork/python/tests/install.tar.gz"]))

      # TODO: figure out how to test when passing the valid packages


      # Set the options so that initialize() throws a "no usable packages" error:
      arizonaconfig.set_option("packagemanagers", "none")
      self.assertEqual([], storkpackage.get_packages_provide([]))
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.get_packages_provide, ['filename'])

      

   #------------------------------------------------------------------
   # get_packages_require():
   #------------------------------------------------------------------
   def test_get_packages_require(self):

      self.assertException(TypeError, storkpackage.get_packages_require, "filename")
      self.assertException(TypeError, storkpackage.get_packages_require, "")
      self.assertException(TypeError, storkpackage.get_packages_require, {})
      self.assertException(TypeError, storkpackage.get_packages_require, ())
      self.assertException(TypeError, storkpackage.get_packages_require, 23)

      # set arizonaconfig to its initial state so that "packagemanagers" options is not set.
      #self.reset_options()
      arizonaconfig.reset()
      #storkpackage.reset()
      self.assertEqual([], storkpackage.get_packages_require([]))
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: missing --packagemanagers setting", storkpackage.get_packages_require, ['filename'])


      # Make the following tests independent of the testing path:
      # Extract the path where "stork/..." starts and leave the part before this substring to a variable
      # that will change so that the tests can be run in different machines:
      prefix = os.environ.get("TESTPREFIX")
      subIdx = prefix.find("stork")
      path = prefix[:subIdx]
      #self.debug_print(path)


      # Set the options so that initialize() does not throw an exception
      self.reset_options()
      self.assertEqual([], storkpackage.get_packages_require(["filename"]))
      self.assertEqual([], storkpackage.get_packages_require([]))
      # subtests with valid rpm and tar packages
      self.debug_print(storkpackage.get_packages_require([path + "stork/testpack/testb-9.1-1.src.rpm"]))
      self.debug_print(storkpackage.get_packages_require([path + "stork/python/tests/install.tar.gz"]))

      # TODO: figure out how to test when passing the valid packages
                                                                                    

      # Set the options so that initialize() throws a "no usable packages" error:
      arizonaconfig.set_option("packagemanagers", "none")
      self.assertEqual([], storkpackage.get_packages_require([]))
      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: no usable package managers.", storkpackage.get_packages_require, ['filename'])

                        

   #------------------------------------------------------------------
   # get_packages_files():
   #------------------------------------------------------------------
   def test_get_packages_files(self):
      # Pass invalid data
      self.assertException(TypeError, storkpackage.get_packages_files, 23)
      self.assertException(TypeError, storkpackage.get_packages_files, ())
      self.assertException(TypeError, storkpackage.get_packages_files, {})
      self.assertException(TypeError, storkpackage.get_packages_files, [[]])
      self.assertException(TypeError, storkpackage.get_packages_files, 'string')
      self.assertException(TypeError, storkpackage.get_packages_files, 23.4)

      # Should simply return an empty list if an empty list is passed:
      self.assertEqual([], storkpackage.get_packages_files( [] ) )

      arizonaconfig.reset()
      storkpackage.reset()
      self.reset_options()


      # Make the following tests independent of the testing path:
      # Extract the path where "stork/..." starts and leave the part before this substring to a variable
      # that will change so that the tests can be run in different machines:
      prefix = os.environ.get("TESTPREFIX")
      subIdx = prefix.find("stork")
      path = prefix[:subIdx]
      #self.debug_print(path)
                                    

      #----------------------- SUBTEST STARTS --------------------------------------------------------------
      # Test with only 'rpm' as a package manager
      arizonaconfig.set_option("packagemanagers", ['rpm'])
      self.assertEqual(['rpm'], arizonaconfig.get_option( "packagemanagers" ) )
      
      # Pass it non-existent files:
      self.assertEqual( [], storkpackage.get_packages_files( [path + "stork/testpack/testb-9.1-1.src.tar"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( [path + "filename"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( ["what"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( ["some", 'unknown', 'file', 'name'] ) )
      
      # Pass it 'tar' packages:
      self.assertEqual( [], storkpackage.get_packages_files( [path + "stork/python/tests/install.tar.gz"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( [path + "stork/testpack/storkd-0.1.0.tar.gz"] ) )
      
      # Pass it 'rpm' packages 
      self.assertFalse(['(contains no files)'] == storkpackage.get_packages_files( [path + "stork/testpack/testb-9.1-1.src.rpm"] ) )
      self.assertFalse(['(contains no files)'] == storkpackage.get_packages_files( [path + "stork/testpack/testb-0.1-1.i386.rpm"] ) )
      self.assertFalse(['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/stork-0.1.0-1.i386.rpm"] ) )
      self.assertFalse(['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/testa-0.2-1.i386.rpm"] ) )
      self.assertFalse(['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/storkd-0.1.0-1.src.rpm"] ) )
      
      #----------------------- SUBTEST ENDS --------------------------------------------------------------
      

      #----------------------- SUBTEST STARTS --------------------------------------------------------------
      # Test with only 'tar' as a package manager
      arizonaconfig.reset()
      storkpackage.reset()
      self.reset_options()
      arizonaconfig.set_option("packagemanagers", ['tar'] )
      self.assertEqual( ['tar'], arizonaconfig.get_option("packagemanagers") )
      
      # Pass it non-existent files:
      self.assertEqual( [], storkpackage.get_packages_files( [path + "stork/testpack/testb.s9.1-1.src.rpm"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( [path + "filename"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( ["what"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( ["some", 'unknown', 'file', 'name'] ) )

      # Pass it 'rpm' packages
      self.assertEqual([], storkpackage.get_packages_files( [path + "stork/testpack/testb-9.1-1.src.rpm"] ) )
      self.assertEqual([], storkpackage.get_packages_files( [path + "stork/testpack/testb-0.1-1.i386.rpm"] ) )
      self.assertEqual([], storkpackage.get_packages_files( [path + "stork/testpack/stork-0.1.0-1.i386.rpm"] ) )
      self.assertEqual([], storkpackage.get_packages_files( [path + "stork/testpack/testa-0.2-1.i386.rpm"] ) )
      self.assertEqual([], storkpackage.get_packages_files( [path + "stork/testpack/storkd-0.1.0-1.src.rpm"] ) )

      # Pass it 'tar' packages
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [ path + "stork/testpack/storkd-0.1.0.tar.gz"] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [ path + "stork/testpack/testa-0.1.tar.gz"] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/testa-0.2.tar.gz"] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/testb-10.1.tar.gz"] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [path + "stork/python/tests/install.tar.gz"] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [path + "stork/python/refactor/package-dir.tar"] ) ) 
                                    
      #----------------------- SUBTEST ENDS --------------------------------------------------------------
      

      #----------------------- SUBTEST STARTS --------------------------------------------------------------
      # Test with both 'rpm' and 'tar' as package managers
      #----------------------- SUBTEST ENDS --------------------------------------------------------------
      arizonaconfig.reset()
      storkpackage.reset()
      self.reset_options()
      self.assertEqual( ['rpm', 'tar'], arizonaconfig.get_option("packagemanagers") )
      
      # Pass it non-existent files:
      self.assertEqual( [], storkpackage.get_packages_files( [path + "stork/testpack/testb.s9.1-1.src.rpm"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( [path + "filename"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( ["what"] ) )
      self.assertEqual( [], storkpackage.get_packages_files( ["some", 'unknown', 'file', 'name'] ) )
      self.assertEqual( [], storkpackage.get_packages_files( [path + "stork/python/refactor/pakage-dir.tar"] ) )

      # Pass it valid 'rpm' and 'tar' files
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [ path + "stork/testpack/storkd-0.1.0.tar.gz"] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [ path + "stork/testpack/testa-0.1.tar.gz"] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/testa-0.2.tar.gz"]) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/testb-10.1.tar.gz" ] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [path + "stork/python/tests/install.tar.gz"] ) )
      self.assertFalse( ['(contains no files)']== storkpackage.get_packages_files( [path + "stork/python/refactor/package-dir.tar"] ) )
                                    
      self.assertFalse(['(contains no files)'] == storkpackage.get_packages_files( [path + "stork/testpack/testb-9.1-1.src.r\
pm"] ) )
      self.assertFalse(['(contains no files)'] == storkpackage.get_packages_files( [path + "stork/testpack/testb-0.1-1.i386.\
rpm"] ) )
      self.assertFalse(['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/stork-0.1.0-1.i386\
.rpm"] ) )
      self.assertFalse(['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/testa-0.2-1.i386.r\
pm"] ) )
      self.assertFalse(['(contains no files)']== storkpackage.get_packages_files( [path + "stork/testpack/storkd-0.1.0-1.src\
.rpm"] ) )

      # (if it contains no files, should return [], not ['(contains no files)']


   #------------------------------------------------------------------
   # get_package_info():
   #------------------------------------------------------------------
   def test_get_package_info(self): #, filename):
      reload(storkpackage)

      # test with invalid input:
      self.assertRaises(TypeError, storkpackage.get_package_info, None)
      self.assertRaises(TypeError, storkpackage.get_package_info, [])
      self.assertRaises(TypeError, storkpackage.get_package_info, ["sdsd"])
      self.assertRaises(TypeError, storkpackage.get_package_info, 23)
      self.assertRaises(TypeError, storkpackage.get_package_info, 56.3)

      self.assertExceptionMessage(arizonageneral.Exception_Data, "ERROR: missing --packagemanagers setting", storkpackage.get_package_info, 'filename')

      self.assertException(Exception, storkpackage.get_package_info)

      # White box: do preparation so that some needed options are initialized 
      # prior to running this method

      # Make the following tests independent of the testing path:
      # Extract the path where "stork/..." starts and leave the part before this substring to a variable
      # that will change so that the tests can be run in different machines:
      prefix = os.environ.get("TESTPREFIX")
      subIdx = prefix.find("stork")
      path = prefix[:subIdx]
      self.debug_print(path)
                                    
      # ---- TEST STARTS ------------------------------------------------------------------------------
      # Test for when the variable "tarpackinfopack" is not set
      self.reset_options()
      self.assertEqual(arizonaconfig.get_option("tarpackinfopath"), "/usr/local/stork/tar_packinfo")
      arizonaconfig.set_option("tarpackinfopath", None)
      self.assertEqual(arizonaconfig.get_option("tarpackinfopath"), None)
      # packagemanagers variable is already set.
      self.assertEquals(['rpm', 'tar'], arizonaconfig.get_option("packagemanagers"))
      # After the call to get_package_info(), only the rpm package manager should be set, since
      # the variable for tar is set to None. Should not raise any excepions and simply return None if the
      # file given is not an rpm package, or the info if it is an rpm package.
      self.assertEqual(storkpackage.get_package_info("filename"), None)
      self.assertEqual(storkpackage.get_package_info(""), None)
      self.assertEqual(storkpackage.get_package_info("."), None)
      # The following two lines make storktar freeze up:
      #self.assertEqual(None, storkpackage.get_package_info("-"))
      #self.assertEqual(None, storkpackage.get_package_info("- "))
      
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0.tar.gz"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testa-0.1.tar.gz"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testa-0.2.tar.gz"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testb-0.1.tar.gz"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testb-10.1.tar.gz"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testb-9.1.tar.gz"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/python/tests/install.tar.gz"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/python/refactor/package-dir.tar"))
                                                
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/stork-0.1.0-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/stork-0.1.0-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.1-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.1-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.2-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.2-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-0.1-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-0.1-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.src.rpm"))

                                                                   
      # ---- TEST ENDS ------------------------------------------------------------------------------
            

      # ---- TEST STARTS ------------------------------------------------------------------------------
      # Prepare the options to test storkpackage: make sure init_options 
      # run successfully but storkpackage.initialize() DOES find 
      # USABLE package managers:

      # set or re-set the options since the tests are not called in order
      self.reset_options()

      # create new option
      arizonaconfig.set_option("packagemanagers", ['rpm', 'tar'])
      self.assertEqual(arizonaconfig.get_option("packagemanagers"), ['rpm', 'tar'])

      # The variable tested below has to be set for tar packages. Note that storkpackage.py will try
      # to create this directory if it does not exist. However, if these tests are run in a restriced
      # profile, then storktar will not be able to create the new directory and the tests will fail.
      # Exchange the original string (the directory that will be created by storktar) with a string
      # that will result in the directory being able to get created in the restriced machine:
      #self.assertEqual("/usr/local/stork/tar_packinfo", arizonaconfig.get_option("tarpackinfopath"))
      arizonaconfig.set_option("tarpackinfopath", path + "/usr/local/stork/tar_packinfo")
                              
      # Now that the options have been successfuly called, 
      # test the method with wrong package names:
      self.assertEqual(None,  storkpackage.get_package_info("some wrong filename"))
      self.assertEqual(None,  storkpackage.get_package_info(""))
      self.assertEqual(None, storkpackage.get_package_info(" "))
      self.assertEqual(None, storkpackage.get_package_info("rpm"))
      self.assertEqual(None, storkpackage.get_package_info("targz"))
      self.assertEqual(None, storkpackage.get_package_info("."))
      # The following two lines make storktar freeze up:
      #self.assertEqual(None, storkpackage.get_package_info("-"))
      #self.assertEqual(None, storkpackage.get_package_info("- "))
            
      # Test the method with correct package names:
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.1.tar.gz"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/stork-0.1.0-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/stork-0.1.0-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.1-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.1-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.2-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.2-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-0.1-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-0.1-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.i386.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.src.rpm"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0.tar.gz"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.1.tar.gz"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testa-0.2.tar.gz"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-0.1.tar.gz"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-10.1.tar.gz"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/testpack/testb-9.1.tar.gz"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/python/tests/install.tar.gz"))
      self.assertTrue(storkpackage.get_package_info(path + "stork/python/refactor/package-dir.tar"))
                                                
      # ---- TEST ENDS ------------------------------------------------------------------------------


      # ---- TEST STARTS ------------------------------------------------------------------------------
      # Check only with 'tar' packages
      arizonaconfig.reset()
      self.reset_options()
      arizonaconfig.set_option("packagemanagers", ['tar'])
      self.assertEqual( ['tar'], arizonaconfig.get_option("packagemanagers"))

      # The variable tested below has to be set for tar packages. Note that storkpackage.py will try

      # The variable tested below has to be set for tar packages. Note that storkpackage.py will try
      # to create this directory if it does not exist. However, if these tests are run in a restriced
      # profile, then storktar will not be able to create the new directory and the tests will fail.
      # Exchange the original string (the directory that will be created by storktar) with a string
      # that will result in the directory being able to get created in the restriced machine:
      #self.assertEqual("/usr/local/stork/tar_packinfo", arizonaconfig.get_option("tarpackinfopath"))
      arizonaconfig.set_option("tarpackinfopath", path + "/usr/local/stork/tar_packinfo")

      # Pass 'rpm' packages
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.src.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/stork-0.1.0-1.i386.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/stork-0.1.0-1.src.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0-1.i386.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0-1.src.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testa-0.1-1.i386.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testa-0.1-1.src.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testa-0.2-1.i386.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testa-0.2-1.src.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testb-0.1-1.i386.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testb-0.1-1.src.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.i386.rpm"))
      self.assertEqual(None, storkpackage.get_package_info(path + "stork/testpack/testb-9.1-1.src.rpm"))
                                                                              
      # Pass 'tar' packages
      self.assertTrue( storkpackage.get_package_info(path + "stork/testpack/storkd-0.1.0.tar.gz"))
      self.assertTrue( storkpackage.get_package_info(path + "stork/testpack/testa-0.1.tar.gz"))
      self.assertTrue( storkpackage.get_package_info(path + "stork/testpack/testa-0.2.tar.gz"))
      self.assertTrue( storkpackage.get_package_info(path + "stork/testpack/testb-0.1.tar.gz"))
      self.assertTrue( storkpackage.get_package_info(path + "stork/testpack/testb-10.1.tar.gz"))
      self.assertTrue( storkpackage.get_package_info(path + "stork/testpack/testb-9.1.tar.gz"))
      self.assertTrue( storkpackage.get_package_info(path + "stork/python/tests/install.tar.gz"))
      self.assertTrue( storkpackage.get_package_info(path + "stork/python/refactor/package-dir.tar"))
                                                
      # ---- TEST ENDS ------------------------------------------------------------------------------
      

      
   #------------------------------------------------------------------
   # get_installed_versions():
   #------------------------------------------------------------------
   def test_get_installed_versions(package_list):
      pass


   #------------------------------------------------------------------
   # get_installedpackages_fulfulling():
   #------------------------------------------------------------------
   def test_get_installedpackages_fulfilling(dep_list):
      pass


   #------------------------------------------------------------------
   # get_installedpackages_provide():
   #------------------------------------------------------------------
   def test_get_installedpackages_provide(package_list):
      pass
  
   #-----------------------------------
   # execute(trans_list)
   #-----------------------------------
   def test_execute(self):
      pass
  
   #-----------------------------------
   # remove(package_list, nodeps=False)
   #-----------------------------------
   def test_remove(self):
      pass



  
      
# Run tests
if __name__ == '__main__':
   arizonaconfig.init_options("storkpackageTest" ) 
   arizonaconfig.set_option("packagemanagers",["rpm"]) 
   arizonaconfig.set_option("hashtype",["-sha1"]) 
   arizonaunittest.main()
