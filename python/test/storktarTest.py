#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: storktar

Author: Updated by Collin Reynolds

Description:   test module for storktar

Note : 
   See storktar for more details
"""


import storktar
import arizonaunittest
import arizonaconfig
import os
import shutil
import arizonageneral
import arizonareport

class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------------------
   # initialize():
   #------------------------------------------------------------------------------
   def test_initialize(self):
      dependencies = storktar.initialize()
      self.assertEquals(dependencies,[])
      
      
      



   #------------------------------------------------------------------------------
   # def is_package_understood(filename):
   #------------------------------------------------------------------------------
   def test_is_package_understood(self):
      self.restore_stdout()
      # A non-string
      self.assertException(TypeError, storktar.is_package_understood, 3)

      # The empty string
      self.assertFalse(storktar.is_package_understood(""))

      # A file that should exist and be readable
      self.assertFalse(storktar.is_package_understood("/bin/ls"))

      # A path
      self.assertFalse(storktar.is_package_understood("/tmp"))

      # An invalid path
      self.assertFalse(storktar.is_package_understood("/jasdfljk/ajsdfjkadf/asjdf"))

      # An invalid file
      self.assertFalse(storktar.is_package_understood("/usr/bin/asjdf"))
      try:
         shutil.copyfile("/bin/ls", "/tmp/test1.tgz")
      except:
         pass
      self.assertFalse(storktar.is_package_understood("/tmp/test1.tgz"))
      os.unlink("/tmp/test1.tgz")
      
      # valid file
      shutil.copyfile(os.getenv("HOME") + "/stork/webpage/example.tar.gz", "/tmp/example.tgz")
      self.assertTrue(storktar.is_package_understood("/tmp/example.tgz"))
      os.unlink("/tmp/example.tgz")
      
      
      
      
      


   #------------------------------------------------------------------------------
   # get_packages_provide(filename_list)
   #------------------------------------------------------------------------------
   def test_get_packages_provide(self):
      deps = storktar.get_packages_provide(["../test/storkendusertar-2.0b-30.tar.gz"])
      self.assertEqual(deps,["storkendusertar = 2.0b-30"])
      deps = storktar.get_packages_provide([])
      self.assertEqual(deps,[])
      deps = storktar.get_packages_provide(["../test/storkendusertar-2.0b-30.tar.gz","../test/example.tar.gz"])
      self.assertEqual(deps,["storkendusertar = 2.0b-30","example = 0.0.0-0"])
      
      
      
      
      
      
   #------------------------------------------------------------------------------   
   # get_packages_require(filename_list)
   #------------------------------------------------------------------------------
   def test_get_packages_require(self):
      # Doesn't return anything yet except an empty list
      self.assertEqual(storktar.get_packages_require([""]),[])
      self.assertException(TypeError,storktar.get_packages_require,123)
      self.assertException(TypeError,storktar.get_packages_require,{})
      self.assertException(TypeError,storktar.get_packages_require,[123])      
      
      
      
      
      
      
   #------------------------------------------------------------------------------   
   # get_packages_files(filename_list)
   #------------------------------------------------------------------------------
   def test_get_packages_files(self):
      # Following needs to be modified so that it goes to the test directory every time
      files = ["../test/example.tar.gz","../test/storkendusertar-2.0b-30.tar.gz"]
      fileList = storktar.get_packages_files(files)
      self.assertEquals(fileList,['example/example.py', 'stork-enduser-tar-2.0b/', 'stork-enduser-tar-2.0b/storkutil.py', 'stork-enduser-tar-2.0b/arizonaconfig.py', 'stork-enduser-tar-2.0b/arizonareport.py', 'stork-enduser-tar-2.0b/storkerror.py', 'stork-enduser-tar-2.0b/arizonacrypt.py', 'stork-enduser-tar-2.0b/arizonaxml.py', 'stork-enduser-tar-2.0b/storkpackage.py', 'stork-enduser-tar-2.0b/arizonageneral.py', 'stork-enduser-tar-2.0b/storkpackagelist.py', 'stork-enduser-tar-2.0b/arizonatransfer.py', 'stork-enduser-tar-2.0b/securerandom.py', 'stork-enduser-tar-2.0b/storktransaction.py', 'stork-enduser-tar-2.0b/comonscript.py', 'stork-enduser-tar-2.0b/package/', 'stork-enduser-tar-2.0b/package/__init__.py', 'stork-enduser-tar-2.0b/package/storktar.py', 'stork-enduser-tar-2.0b/package/storkrpm.py', 'stork-enduser-tar-2.0b/package/storknestrpm.py', 'stork-enduser-tar-2.0b/default.publickey', 'stork-enduser-tar-2.0b/sample-stork.conf'])
      
      
      
      
      
      
      
   #------------------------------------------------------------------------------   
   # get_package_info(filename)
   #------------------------------------------------------------------------------   
   def test_get_package_info(self):
      filename = "../test/storkendusertar-2.0b-30.tar.gz"
      infoList = storktar.get_package_info(filename)
      self.assertEquals(infoList,['storkendusertar', '2.0b', '30', '419163'])
      
      filename = "../test/example.tar.gz"
      infoList = storktar.get_package_info(filename)
      self.assertEquals(infoList,['example', '0.0.0', '0', '1423'])      
      
      
      
      
      

   #------------------------------------------------------------------------------
   # get_package_names(filename_list):
   # Not implemented yet
   #------------------------------------------------------------------------------
   def test_get_package_names(self):
      pass
      
      
      
      
      
      
   #------------------------------------------------------------------------------
   # get_installedpackages_fulfilling(dep_list):
   #------------------------------------------------------------------------------
   def test_get_installedpackages_fulfilling(self): 
      # create a info file 
      packinfo_dir = arizonaconfig.get_option("tarpackinfopath")
      if not os.path.exists(packinfo_dir):
         os.mkdir(packinfo_dir)
      testpack1 = "testpack1.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack1, "w")
      tempfile.write("testing1\nversion\n3.5\nTest pack")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installedpackages_fulfilling(["testpack1"]), ["testing1-version-3.5"])      

      # create another info file
      testpack2 = "testpack2.tgz.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack2, "w")
      tempfile.write("testing2\nversion\n3.14\nTest pack")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installedpackages_fulfilling(["testpack2"]), ["testing2-version-3.14"])      
      
      # create 3rd info file
      testpack3 = "testpack3.tar.gz.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack3, "w")
      tempfile.write("testing3\nversion\n2.93\nTest pack3")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installedpackages_fulfilling(["testpack3"]), ["testing3-version-2.93"])      

      # put these files all together
      self.assertEqual(storktar.get_installedpackages_fulfilling(["testpack1", "testpack2", "testpack3"]), ['testing1-version-3.5', 'testing2-version-3.14', 'testing3-version-2.93'])      

      # some packages of the package list don't exist
      self.assertEqual(storktar.get_installedpackages_fulfilling(["testpack1", "rpm", "testpack2", "ls",  "nano", "testpack3"]), 
                                                         ['testing1-version-3.5', 'testing2-version-3.14', 'testing3-version-2.93'])            
      

      # remove testing files and directory
      os.remove(packinfo_dir + "/" + testpack1)
      os.remove(packinfo_dir + "/" + testpack2)
      os.remove(packinfo_dir + "/" + testpack3)
      os.rmdir(packinfo_dir)
      
      
      
      
      

   #------------------------------------------------------------------------------
   # get_installedpackages_provide(package_list):
   #------------------------------------------------------------------------------
   def test_get_installedpackages_provide(self):
      # create a info file 
      packinfo_dir = arizonaconfig.get_option("tarpackinfopath")
      if not os.path.exists(packinfo_dir):
         os.mkdir(packinfo_dir)
      testpack1 = "testpack1.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack1, "w")
      tempfile.write("testing1\nversion\n3.5\nTest pack")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installedpackages_provide(["testpack1"]), ["testing1 = version-3.5"])      

      # create another info file
      testpack2 = "testpack2.tgz.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack2, "w")
      tempfile.write("testing2\nversion\n3.14\nTest pack")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installedpackages_provide(["testpack2"]), ["testing2 = version-3.14"])      
      
      # create 3rd info file
      testpack3 = "testpack3.tar.gz.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack3, "w")
      tempfile.write("testing3\nversion\n2.93\nTest pack3")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installedpackages_provide(["testpack3"]), ["testing3 = version-2.93"])      

      # put these files all together
      self.assertEqual(storktar.get_installedpackages_provide(["testpack1", "testpack2", "testpack3"]), ['testing1 = version-3.5', 'testing2 = version-3.14', 'testing3 = version-2.93'])      

      # some packages of the package list don't exist
      self.assertEqual(storktar.get_installedpackages_provide(["testpack1", "rpm", "testpack2", "ls",  "nano", "testpack3"]), 
                                                         ['testing1 = version-3.5', 'testing2 = version-3.14', 'testing3 = version-2.93'])            
      

      # remove testing files and directory
      os.remove(packinfo_dir + "/" + testpack1)
      os.remove(packinfo_dir + "/" + testpack2)
      os.remove(packinfo_dir + "/" + testpack3)
      os.rmdir(packinfo_dir)
      
      
      
      
      

   #------------------------------------------------------------------------------
   # get_installed_versions(package_list):
   #------------------------------------------------------------------------------
   def test_get_installed_versions(self):
      self.restore_stdout()
      # A non-string
      self.assertException(TypeError, storktar.get_installed_versions, 3)
      # a list of ints
      self.assertException(TypeError, storktar.get_installed_versions, [3, 5, 7])
      
      # obviously not-existing package
      self.assertEqual(storktar.get_installed_versions([""]), [])      

      # another not-existing package
      self.assertEqual(storktar.get_installed_versions(["rpm"]), [])      

      # create a info file 
      packinfo_dir = arizonaconfig.get_option("tarpackinfopath")
      if not os.path.exists(packinfo_dir):
         os.mkdir(packinfo_dir)
      testpack1 = "testpack1.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack1, "w")
      tempfile.write("testing1\nversion\n3.5\nTest pack")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installed_versions(["testpack1"]), ["testing1 = version-3.5"])      

      # create another info file
      testpack2 = "testpack2.tgz.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack2, "w")
      tempfile.write("testing2\nversion\n3.14\nTest pack")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installed_versions(["testpack2"]), ["testing2 = version-3.14"])      
      
      # create 3rd info file
      testpack3 = "testpack3.tar.gz.packinfo"
      tempfile = file(packinfo_dir + "/"+ testpack3, "w")
      tempfile.write("testing3\nversion\n2.93\nTest pack3")
      tempfile.close()
      
      # check it with package name 'testpack1'
      self.assertEqual(storktar.get_installed_versions(["testpack3"]), ["testing3 = version-2.93"])      

      # put these files all together
      self.assertEqual(storktar.get_installed_versions(["testpack1", "testpack2", "testpack3"]), ['testing1 = version-3.5', 'testing2 = version-3.14', 'testing3 = version-2.93'])      

      # some packages of the package list don't exist
      self.assertEqual(storktar.get_installed_versions(["testpack1", "rpm", "testpack2", "ls",  "nano", "testpack3"]), 
                                                         ['testing1 = version-3.5', 'testing2 = version-3.14', 'testing3 = version-2.93'])            
      

      # remove testing files and directory
      os.remove(packinfo_dir + "/" + testpack1)
      os.remove(packinfo_dir + "/" + testpack2)
      os.remove(packinfo_dir + "/" + testpack3)
      os.rmdir(packinfo_dir)
      
      
      
      

   #------------------------------------------------------------------------------      
   # get_installedpackages_requiring(deplist)
   # not implemented yet
   #------------------------------------------------------------------------------
   def test_get_installedpackages_requiring(self):
      pass
      
      
      
      
      

   #------------------------------------------------------------------------------      
   # get_installedpackages()
   # not implemented
   #------------------------------------------------------------------------------
   def test_get_installedpackages(self):
      pass
      
      
      
      
      


   #------------------------------------------------------------------------------   
   # get_installedpackages_requires(package_list)
   # not implemented
   #------------------------------------------------------------------------------
   def test_get_installedpackages_requires(self):
      pass   
      
      
      
      
      

   #------------------------------------------------------------------------------      
   # execute(trans_list):
   #------------------------------------------------------------------------------
   def test_execute(self):
      import storktransaction
      tl = storktransaction.tl_create()
      #Just test a blank transaction list to execute
      storktar.execute(tl)      
      
      
      
      
      
      
      
      
      
   #------------------------------------------------------------------------------      
   # determine_package_type_no_re(filename)
   #------------------------------------------------------------------------------
   def test_determine_package_type_no_re(self):
      self.assertEqual(storktar.determine_package_type_no_re("../test/example.tar.gz"),"z")
      
      
      
      
      


   #------------------------------------------------------------------------------
   # remove(package_list):
   #------------------------------------------------------------------------------
   def test_remove(self):
      self.restore_stdout()
      # A non-string
      self.assertException(TypeError, storktar.remove, 3)
      # a list of ints
      self.assertException(TypeError, storktar.remove, [3, 5, 7])

      # The empty string
      self.assertException(arizonageneral.Exception_Data ,storktar.remove, [""])

      # invalid package name
      self.assertException(arizonageneral.Exception_Data ,storktar.remove, ["dhsfkj"])



   def __check_files(self, pack):
      (out, err, status) = arizonageneral.popen5("tar -Pztf " + pack)

      if out[0][0] != "/":
         path_head = os.getenv("HOME") + "/"
      else:
         path_head = ""

      for afile in out:
         afile = afile.strip('\n')

         if not os.path.exists(path_head + afile):
            print "\nsome of files on package " + pack + " has not installed"
            os._exit(1)

#=====================================================================
# Run tests
#=====================================================================
if __name__=='__main__':
   arizonaconfig.init_options("tarpackinfopath") 
   arizonaconfig.set_option("tarpackinfopath", "/tmp/tar_packinfo")
   arizonaunittest.main()
