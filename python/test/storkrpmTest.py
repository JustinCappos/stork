#! /usr/bin/env python
"""
<Module>
   storkrpmTest
<Author>
   Jeffry Johnston, under the direction of Justin Cappos
   Rewritten by Collin Reynolds
<Started>
   September 29, 2005   
<Purpose>
   Test module for storkrpm.  See storkrpm.py for more details.
"""

import arizonaunittest
import storkrpm
import os
import arizonaconfig
import arizonatransfer

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------
   # initialize() -> void
   #------------------------------------------------------------------
   def test_initialize(self):
      # note: this test will fail as the version of rpm changes 
      self.assertEqual(storkrpm.initialize(), 
                       ['rpmlib(VersionedDependencies) = 3.0.3-1', 'rpmlib(CompressedFileNames) = 3.0.4-1', 
                        'rpmlib(PayloadIsBzip2) = 3.0.5-1', 'rpmlib(PayloadFilesHavePrefix) = 4.0-1', 
                        'rpmlib(ExplicitPackageProvide) = 4.0-1', 'rpmlib(HeaderLoadSortsTags) = 4.0.1-1', 
                        'rpmlib(ScriptletInterpreterArgs) = 4.0.3-1', 'rpmlib(PartialHardlinkSets) = 4.0.4-1', 
                        'rpmlib(ConcurrentAccess) = 4.1-1', 'rpmlib(BuiltinLuaScripts) = 4.2.2-1'])
   




   #------------------------------------------------------------------
   # is_package_understood(filename)
   # filename -> bool, TypeError
   #------------------------------------------------------------------
   def test_is_package_understood(self): 
      # A non-string
      self.assertException(TypeError, storkrpm.is_package_understood, 3)

      # The empty string
      self.assertFalse(storkrpm.is_package_understood(""))

      # A file that should exist and be readable
      self.assertFalse(storkrpm.is_package_understood("/bin/ls"))

      # A path
      self.assertFalse(storkrpm.is_package_understood("/tmp"))

      # An invalid path
      self.assertFalse(storkrpm.is_package_understood("/jasdfljk/ajsdfjkadf/asjdf"))

      # An invalid file
      self.assertFalse(storkrpm.is_package_understood("/usr/bin/asjdf"))
      
      # A misnamed file
      os.system("cp /bin/ls /tmp/ls.rpm")
      self.assertFalse(storkrpm.is_package_understood("/tmp/ls.rpm"))
      os.system("rm /tmp/ls.rpm")

      # A real rpm
      self.assertTrue(os.path.isfile("../test/PyXML-0.8.3-6.i386.rpm"))
      self.assertTrue(storkrpm.is_package_understood("../test/PyXML-0.8.3-6.i386.rpm"))
                                                  
      # A real rpm that has been corrupted
      os.system('cp ../test/PyXML-0.8.3-6.i386.rpm ../test/Corrupted.rpm')
      os.system('echo "abcTestingcorrupted" > ../test/Corrupted.rpm')
      self.assertFalse(storkrpm.is_package_understood("../test/Corrupted.rpm"))
      os.remove("../test/Corrupted.rpm")
      
      
      
      
      
      
   #------------------------------------------------------------------
   # get_packages_provide(filename_list)
   #------------------------------------------------------------------   
   def test_get_packages_provide(self):
      #test normal input
      dep_list = storkrpm.get_packages_provide(["../test/PyXML-0.8.3-6.i386.rpm"])
      self.assertEqual(dep_list,['boolean.so', 'pyexpat.so', 'sgmlop.so', 'PyXML = 0.8.3-6'])
      
      #test errors
      self.assertException(TypeError,storkrpm.get_packages_provide,"../test/PyXML-0.8.3-6.i386.rpm")
      self.assertException(TypeError,storkrpm.get_packages_provide,{"filename":"../test/PyXML-0.8.3-6.i386.rpm"})
      self.assertException(TypeError,storkrpm.get_packages_provide,None)
      self.assertException(TypeError,storkrpm.get_packages_provide,356)
      self.assertException(TypeError,storkrpm.get_packages_provide,[123])
      
      
      
      
      
   #------------------------------------------------------------------
   # get_packages_require(filename_list)
   #------------------------------------------------------------------
   def test_get_packages_require(self):
      #test normal input
      dep_list = storkrpm.get_packages_require(["../test/PyXML-0.8.3-6.i386.rpm"])
      self.assertEqual(dep_list,['/usr/bin/python', 'libc.so.6', 'libc.so.6(GLIBC_2.0)', 
                                 'libc.so.6(GLIBC_2.1.3)', 'libc.so.6(GLIBC_2.3)', 
                                 'libpthread.so.0', 'python', 'rpmlib(CompressedFileNames) <= 3.0.4-1', 
                                 'rpmlib(PayloadFilesHavePrefix) <= 4.0-1'])
      
      #test errors
      self.assertException(TypeError,storkrpm.get_packages_require,"../test/PyXML-0.8.3-6.i386.rpm")
      self.assertException(TypeError,storkrpm.get_packages_require,{"filename":"../test/PyXML-0.8.3-6.i386.rpm"})
      self.assertException(TypeError,storkrpm.get_packages_require,None)
      self.assertException(TypeError,storkrpm.get_packages_require,356)
      self.assertException(TypeError,storkrpm.get_packages_require,[123])                                     
      
      
      
      
      
   #------------------------------------------------------------------
   # get_packages_files(filename_list)
   #------------------------------------------------------------------
   def test_get_packages_files(self):
      #test normal input
      self.assertTrue(os.path.isfile("../test/PyXML-0.8.3-6.i386.rpm"))
      os.system("rpm -qpl ../test/PyXML-0.8.3-6.i386.rpm > ../test/rpmoutput.dat")
      pack_files = storkrpm.get_packages_files(["../test/PyXML-0.8.3-6.i386.rpm"])
      
      compare_list = []
      for line in file("../test/rpmoutput.dat","r"):
         compare_list.append(line.strip("\n"))
         
      self.assertEqual(pack_files,compare_list)
      os.remove("../test/rpmoutput.dat")
      
      #test errors
      self.assertException(TypeError,storkrpm.get_packages_files,"../test/PyXML-0.8.3-6.i386.rpm")
      self.assertException(TypeError,storkrpm.get_packages_files,{"filename":"../test/PyXML-0.8.3-6.i386.rpm"})
      self.assertException(TypeError,storkrpm.get_packages_files,None)
      self.assertException(TypeError,storkrpm.get_packages_files,356)
      self.assertException(TypeError,storkrpm.get_packages_files,[123])
      
      
      
      
      
   #------------------------------------------------------------------      
   # get_package_info(filename)
   #------------------------------------------------------------------
   def test_get_package_info(self):
      #test normal input
      pack_info = storkrpm.get_package_info("../test/PyXML-0.8.3-6.i386.rpm")
      self.assertEqual(pack_info, ['PyXML', '0.8.3', '6', '6944287'])
      
      #test errors
      self.assertException(TypeError,storkrpm.get_package_info,["../test/PyXML-0.8.3-6.i386.rpm"])
      self.assertException(TypeError,storkrpm.get_package_info,{"filename":"../test/PyXML-0.8.3-6.i386.rpm"})
      self.assertException(TypeError,storkrpm.get_package_info,None)
      self.assertException(TypeError,storkrpm.get_package_info,356)
      self.assertException(TypeError,storkrpm.get_package_info,[123])    
      
      
      
      
      
      
   #------------------------------------------------------------------
   # get_installed_versions(package_list)
   #------------------------------------------------------------------
   def test_get_installed_versions(self):
      #test normal input
      version_list = storkrpm.get_installed_versions(["PyXML"])
      self.assertEqual(version_list,['PyXML = 0.8.4-4'])
      
      #test errors
      self.assertException(TypeError,storkrpm.get_installed_versions,"PyXML")
      self.assertException(TypeError,storkrpm.get_installed_versions,{"package":"PyXML"})
      self.assertException(TypeError,storkrpm.get_installed_versions,None)
      self.assertException(TypeError,storkrpm.get_installed_versions,356)
      self.assertException(TypeError,storkrpm.get_installed_versions,[123])    
      
      

      
   #------------------------------------------------------------------      
   # get_installedpackages_requiring(dep_list)
   #------------------------------------------------------------------
   def test_get_installedpackages_requiring(self):
      dep_list = storkrpm.get_packages_require(["../test/PyXML-0.8.3-6.i386.rpm"])
      #somehow test that this worked...
      #self.assertEqual(storkrpm.get_installedpackages_requiring(dep_list),some huge list of packages)
      
      
      
      
      
      
   #------------------------------------------------------------------
   # get_installedpackages_fulfilling(dep_list)
   # dep_list -> package_list, TypeError   
   #------------------------------------------------------------------
   def test_get_installedpackages_fulfilling(self):
      # Not a string list
      self.assertException(TypeError, storkrpm.get_installedpackages_provide, "abc")
      
      # test with installed packages
      self.assertEqual(storkrpm.get_installedpackages_fulfilling(["filesystem", "coreutils"]),
                        ['filesystem-2.4.0-1', 'coreutils-5.97-12.5.fc6'])
                        
                        
                        
                        
     
   #------------------------------------------------------------------                        
   # get_installedpackages()                        
   #------------------------------------------------------------------
   def test_get_installedpackages(self):
      #Test normal input
      out = os.popen("rpm -q -a")
      compare_list = []
      for line in out:
         compare_list.append(line.strip("\n"))
         
      self.assertEqual(storkrpm.get_installedpackages(),compare_list)
      
      
      
      
      
         
   #------------------------------------------------------------------
   # package_list -> dep_list, IOError, TypeError      
   #------------------------------------------------------------------
   def test_get_installedpackages_provide(self):
      # note: this test will fail as the version of rpm changes 

      # Not a string list
      self.assertException(TypeError, storkrpm.get_installedpackages_provide, "abc")

      # test with installed packages
      self.assertEqual(storkrpm.get_installedpackages_provide(["coreutils"]), ['config(coreutils) = 5.97-12.5.fc6', 'fileutils = 5.97', 'sh-utils = 5.97', 'stat', 'textutils = 5.97', 'coreutils = 5.97-12.5.fc6'])
      
      
      
      
      
   
   #------------------------------------------------------------------
   # get_installedpackages_requires(package_list)   
   #------------------------------------------------------------------
   def test_get_installedpackages_requires(self):
      pass
      
      
      
      
      
   #------------------------------------------------------------------
   # check_install_status(filename_list)
   #------------------------------------------------------------------
   def test_check_install_status(self):
      self.assertEqual(storkrpm.check_install_status(["../test/PyXML-0.8.3-6.i386.rpm"]),([],["PyXML"]))   
      #Needs more work
      
      
      
      
      
      
   #------------------------------------------------------------------
   # execute(trans_list)
   #------------------------------------------------------------------
   def test_execute(self):
      import storktransaction
      # check params: Not a string list
      self.assertException(TypeError, storkrpm.get_installedpackages_provide, "abc")
      
      try:
         storkrpm.remove("PyXML")
      except:
         pass
      
      # install package
      self.assertTrue(os.path.isfile("../test/PyXML-0.8.3-6.i386.rpm"))
      tl = storktransaction.tl_create()
      storktransaction.tl_install(tl,"../test/PyXML-0.8.3-6.i386.rpm")
      storkrpm.execute(tl)





   #------------------------------------------------------------------
   # package_list -> void, IOError, NameError, TypeError
   #------------------------------------------------------------------
   def test_remove(self):
      pass

 
""" 
      self.assertException(TypeError, arizonaconfig.init_options, 100)
      self.set_cmdline(["--help"])
      self.reset_stdout()
      self.reset_stderr()
      reload(arizonaconfig)
"""

# Run tests
if __name__ == '__main__':
   storkrpm.initialize()
   arizonaconfig.init_options("storkrpmTest") 
   arizonaconfig.set_option("transfermethod", ['http', 'ftp'])
   arizonaunittest.main()
