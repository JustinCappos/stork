#! /usr/bin/env python
"""
<Module>
   storkpackagelistTest
<Author>
   Jeffry Johnston, under the direction of Justin Cappos

   Extended by Mario Gonzalez.

<Started>
   October 13, 2005   
<Purpose>
   Test module for storkpackagelist.  See storkpackagelist.py for more 
   details.
"""

import os
import arizonaconfig
import arizonatransfer
import arizonaunittest
import storkpackagelist

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------
   # reset_options()
   #------------------------------------------------------------------
   def reset_options(self):
      self.set_cmdline([])
      prefix = os.environ.get("TESTPREFIX")
      #reload(storkpackagelist)
      arizonaconfig.init_options("storkpackagelist.py", alt_paths=[prefix], version="2.0")


   #------------------------------------------------------------------
   # init():
   #------------------------------------------------------------------
   def test_init(self):
      self.reset_options()
      prefix = os.getenv('TESTPREFIX')

      # test without initializing the "pdir" option:
      self.assertException(SystemExit, storkpackagelist.init)

      # test without initializing the "repinfo" option:
      arizonaconfig.init_options("storkpackagelist.py", alt_paths = [prefix], version='2.0')
      arizonaconfig.set_option("pdir", ["nr06.cs.arizona.edu/PlanetLab/V3/dist"])
      self.assertException(SystemExit, storkpackagelist.init)
      self.reset_options()


      # test with both options initialized. Test with "updatedb" unset.
      arizonaconfig.init_options("storkpackagelist.py", alt_paths = [prefix], version='2.0')
      # shouldn't init_options() set all the variables by itself?
      # NOTE that currently, if "updatedb" variable is not set manually, then calling get_option("updatedb") returns None.
      arizonaconfig.set_option("pdir", ["nr06.cs.arizona.edu/PlanetLab/V3/dist"])
      arizonaconfig.set_option("repinfo", ["nr06.cs.arizona.edu/packageinfo"])
      # localpdir will now be populated with "nr06.cs.arizona.edu_PlanetLab_V3_dist" and set_option will be called
      # with the string  "localpdir" and the newly created list.
      # Since the variable "localinfo" has not been set yet, it should give an error
      #self.assertException(TypeError, storkpackagelist.init)
      # now set the "localinfo" variable and call init().
      arizonaconfig.set_option("localinfo", "/usr/local/stork/var/packageinfo")
      storkpackagelist.init()
      self.assertEquals(["nr06.cs.arizona.edu_PlanetLab_V3_dist"], arizonaconfig.get_option("localpdir"))
            
   
      # Manually set "updatedb" to false and test init()
      self.reset_options()
      arizonaconfig.set_option("updatedb", False)
      arizonaconfig.set_option("pdir", ["nr06.cs.arizona.edu/PlanetLab/V3/dist"])
      arizonaconfig.set_option("repinfo", ["nr06.cs.arizona.edu/packageinfo"])
      # localpdir will now be populated with "nr06.cs.arizona.edu_packageinfo" and set_option will be called
      # with the string  "localpdir" and the newly created list.
      # Since the variable "localinfo" has not been set yet, it should give an error
      self.assertException(TypeError, storkpackagelist.init)
      # now set the "localinfo" variable and call init().
      arizonaconfig.set_option("localinfo", "/usr/local/stork/var/packageinfo")
      storkpackagelist.init()
      self.assertEquals(["nr06.cs.arizona.edu_PlanetLab_V3_dist"], arizonaconfig.get_option("localpdir"))
      

      # Manually set "updatedb" to true and test init()
      self.reset_options()
      arizonaconfig.set_option("updatedb", True)
      arizonaconfig.set_option("pdir", ["nr06.cs.arizona.edu/PlanetLab/V3/dist"])
      arizonaconfig.set_option("repinfo", ["nr06.cs.arizona.edu/packageinfo"])
      # Since the variable "localinfo" has not been set yet, it should give an error
      self.assertException(TypeError, storkpackagelist.init)
      # now set the "localinfo" variable and call init().
      arizonaconfig.set_option("localinfo", "/usr/local/stork/var/packageinfo")
      storkpackagelist.init()
      self.assertEquals(["nr06.cs.arizona.edu_PlanetLab_V3_dist"], arizonaconfig.get_option("localpdir"))

      

      # TODO: test that a database directory for "nr06.cs.arizona.edu_packageinfo" is found AND also
      # TODO: test that a database directory for "nr06.cs.arizona.edu_packageinfo" is NOT found


      # Assuming a database directory is found:
      # If the option "updatedb" is true in the arizonaconfig block of storkpackagelist, then
      # the package info (the metadata) will be updated.
      #
      # TODO: make sure package files are not retrieved successfully and get the error report

      # TODO: make sure package files ARE retrieved successfully and report.
      

      # Test when updatedb is set to FALSE
      reload(storkpackagelist)
      arizonaconfig.init_options("storkpackagelist.py")
      arizonaconfig.set_option("updatedb", False)
      arizonaconfig.set_option("pdir", ["nr06.cs.arizona.edu/PlanetLab/V3/dist"])
      arizonaconfig.set_option("repinfo", ["nr06.cs.arizona.edu/packageinfo"])
      storkpackagelist.init()                     


      # Now test everything above without manually setting the options for storkpackagelist: that is,
      # only use arizonaconfig.init_options(..)
      # TODO:

            
      # NOT SURE IF IT STILL APPLIES:
      # CURRENTLY, init() only works if set_option() is used explicitly with "localinfo".
      # Should work fine without this, though.
      #arizonaconfig.set_option("localinfo", "some path")
      storkpackagelist.init()
      #except:
         # is it that it could not locate a database directory for some option?
         # TODO: figure out how to get the send_error() messages
         ## Let's see what "localpdir" returns (the assertion failure, if any, will contain the return value):
         #self.assertEquals(None, arizonaconfig.get_option("localpdir"))
         #pass


   #------------------------------------------------------------------
   # package_exists():
   #------------------------------------------------------------------
   def test_package_exists(self):
      self.reset_options()
      

      # should return None if None is passed:
      self.assertEquals(None, storkpackagelist.package_exists(None))

      # pass invalid input
      self.assertRaises(Exception, storkpackagelist.package_exists, 3.0)

      # ON HOLD-- docs may be wrong
      ## pass names that are not known packages without initializing the options.
      ## Should return None:
      #self.assertEquals(None, storkpackagelist.package_exists(" "))
      #self.assertEquals(None, storkpackagelist.package_exists("some unknown package"))

      # pass names that are not known packages, but initialize options first
      # since arizonaconfig.get_options() is used:
      prefix = os.environ.get("TESTPREFIX")
      arizonaconfig.init_options("storkpackagelist.py", alt_paths=[prefix], version='2.0')
      #arizonaconfig.set_option("localpdir", ["some string"]) <- this should not be set manually
      # now set the "localinfo" variable and call init().
      arizonaconfig.set_option("localinfo", "/usr/local/stork/var/packageinfo")
      arizonaconfig.set_option("pdir", ["nr06.cs.arizona.edu/PlanetLab/V3/dist"])
      arizonaconfig.set_option("repinfo", ["nr06.cs.arizona.edu/packageinfo"])
      storkpackagelist.init()
      self.assertFalse(storkpackagelist.package_exists("hello"))
      self.assertFalse(storkpackagelist.package_exists("some unknown name"))
      self.assertFalse(storkpackagelist.package_exists("gnuchess"))
      self.assertFalse(storkpackagelist.package_exists(" "))

      # this test was from Jeffry Johnston.
      # NOTE that currently, it only works if the metadata exists on the system.
      arizonaconfig.init_options("storkpackagelist.py", alt_paths = [prefix], version = '2.0')
      arizonaconfig.set_option("updatedb", False)
      arizonaconfig.set_option("pdir", ["nr06.cs.arizona.edu/PlanetLab/V3/dist/"])
      arizonaconfig.set_option("repinfo", ["nr06.cs.arizona.edu/packageinfo"])
      storkpackagelist.init()
      self.assertTrue(storkpackagelist.package_exists("gnuchess"))
      


   #------------------------------------------------------------------------------------
   # find_package_name()
   #------------------------------------------------------------------------------------
   def test_find_package_name(self):

      self.reset_options()

      # set the options needed by storkpackagelist.init()
      arizonaconfig.set_option("pdir", ["nr06.cs.arizona.edu/PlanetLab/V3/dist"])
      arizonaconfig.set_option("repinfo", ["nr06.cs.arizona.edu/packageinfo"])
      storkpackagelist.init()
      self.assertEquals( "/usr/local/stork/var/packageinfo", arizonaconfig.get_option("localinfo") )
      # init() should have set the localpdir variable

      # Should return None if nothing is found
      self.assertEquals(None, storkpackagelist.find_package_name('stork'))
      self.assertEquals(None, storkpackagelist.find_package_name(''))
      self.assertEquals(None, storkpackagelist.find_package_name(' '))
      self.assertEquals(None, storkpackagelist.find_package_name('-'))
      self.assertEquals(None, storkpackagelist.find_package_name('.'))
      self.assertEquals(None, storkpackagelist.find_package_name('23'))
      


      # Pass it a valid, existent, filename
      # Since grep is called with the instruction:
      #      out, err, status = arizonageneral.popen5("grep -rl ^" + field + ":" + search + " " + os.path.join(arizonaconfig.get_option("localinfo"), package_dir))                               
      # set the variables to the variable "localinfo" and "localpdir" to point to the directory where the packages are:
      # TODO arizonaconfig.set_option( "pdir", ["stork"] )
      # TODO arizonaconfig.set_option( "localinfo", "/usr/local/stork/" )      
      self.assertEquals(None, storkpackagelist.find_package_name("storkd-0.1.0-1.src.rpm") )


   #------------------------------------------------------------------------------------
   # find_packages()
   #------------------------------------------------------------------------------------
   def test_find_packages(self):
      pass



   #------------------------------------------------------------------------------------
   # __find_package_fnlist_on_one_criteria()
   #------------------------------------------------------------------------------------
#   def test___find_package_fnlist_on_one_criteria(self):
#      _test._storkpackagelist__find_package_fnlist_on_one_criteria('filename', 'stork')

                  

               
   
      
   #------------------------------------------------------------------
   # cull_database(items, fields): ->
   #------------------------------------------------------------------
   def test_cull_database(self):
      pass

   #------------------------------------------------------------------
   # get_field(field): ->
   #------------------------------------------------------------------
   def test_get_field(self):
      pass

   #------------------------------------------------------------------
   # get_db_field(string,field): ->
   #------------------------------------------------------------------
   def test_get_db_field(self):
      pass

   #------------------------------------------------------------------
   # package_cache_name(pkg_db): -> string
   #------------------------------------------------------------------
   def test_package_cache_name(self):
      pass
      
   #------------------------------------------------------------------
   # which_pdir(line): -> string or None
   #------------------------------------------------------------------
   def test_which_pdir(self):
      pass

   #------------------------------------------------------------------
   # check_package(name): -> True/False, None (error)
   #------------------------------------------------------------------
   def test_check_package(self):
      pass

# Run tests
if __name__ == '__main__':
   arizonaconfig.init_options("storkpackagelist.py") 
   arizonaunittest.main()
