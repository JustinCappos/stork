#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: storktransferTest
Description:   test module for arizonatransfer

Notes:
   See arizonatransfer for more details
"""

import arizonatransfer
import arizonaunittest
import arizonaconfig
import os
import shutil
import sys


class test(arizonaunittest.TestCase):

   # host where files to be retrieved are located
   host = 'quadrus.cs.arizona.edu/test'

   # temp directory where retrieved files will be placed
   tmp_dir = '/tmp/transfer_testdir/'
   
   # public key trusted to sign signed metafiles
   repkey = 'MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAN5k8fLj76b5N03XmQtlYc+XayJEXTIRzI5S1tVuig8mKyQL+qAHboCCvCzZy3lM+m5zY95JD8ZAXI1s65i0pasCAwEAAQ=='

   # a different public key to use in tests
   repkey2 = 'MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAK+Exd/TTewKInvDsec9vkpHUTpWNM8MqwQA/0nokIkoN7PIEVj8ojcwfuz5fUzUJGHJ0rx4Q0RJVii6I9ULkckCAwEAAQ=='


   #------------------------------------------------------------------------------
   # getfiles(host, filelist, destdir, prog_indicator=False):
   #------------------------------------------------------------------------------
   def test_getfiles(self):
    
      # TODO: decide what should be used here in the general arizonatransfer tests
      arizonaconfig.set_option("transfermethod", ['coblitz'])
      arizonaconfig.set_option("tarpackinfopath", "/tmp/stork_trans_tmp")
    
      #self.restore_stdout()
      
      host = self.host
      tmp_dir = self.tmp_dir
    
      # ensure temp directory exists and is empty
      if os.path.exists(tmp_dir):
          shutil.rmtree(tmp_dir)
      os.makedirs(tmp_dir)
    
      ####### get a single file
      
      files = ['cpio-2.5-6.i386.rpm']
      expected_result_files = self.__get_expected_result_files(files)
      
      self.assertEqual(arizonatransfer.getfiles(host, files, tmp_dir), (True, expected_result_files))
      self.__remove_files(expected_result_files) # clean up files

      ####### get multiple files

      files = ['cpio-2.5-6.i386.rpm', 'BitTorrent-4.0.4-1.noarch.rpm', 'testfile']
      expected_result_files= self.__get_expected_result_files(files)

      self.assertEqual(arizonatransfer.getfiles(host, files, tmp_dir), (True, expected_result_files))
      self.__remove_files(expected_result_files) # clean up files

      ####### get multiple files where one of the files is repeated
      ####### TODO: fix this, it isn't working. what is expected behaviour?

#      files = ['PyXML-0.8.3-6.i386.rpm', 'BitTorrent-4.0.4-1.noarch.rpm', 'testfile', 'testfile']
#      expected_result_files= self.__get_expected_result_files(files)
#
#      self.assertEqual(arizonatransfer.getfiles(host, files, tmp_dir), (True, expected_result_files))
#      self.__remove_files(expected_result_files) # clean up files

      ####### if the file list has a directory in the name, the file should be put in
      ####### that directory (according to old unit test by Justin C)
      ####### TODO: fix this, it isn't working. is this still expected behaviour?

#      files = ['sync_test1/metafile']
#      expected_result_files= self.__get_expected_result_files(files)
#      
#      self.assertEqual(arizonatransfer.getfiles(host, files, tmp_dir), (True, expected_result_files))
#      self.__remove_files(expected_result_files) # clean up files
      
      ####### test error: host is not a string

      non_string_host = 3
      files = ['testfile']
      self.assertException(TypeError, arizonatransfer.getfiles, non_string_host, files, tmp_dir)

      ####### test error: can't connect to host

      invalid_host = "invalidhostname"
      self.assertEqual(arizonatransfer.getfiles(invalid_host, files, tmp_dir), (False, []))
      
      ####### test error: host doesn't have the files

      host_without_files = host + "/nonexistent_directory"
      self.assertEqual(arizonatransfer.getfiles(host_without_files, files, tmp_dir), (False, []))
   
      ####### test error: filelist is not a list 

      self.assertException(TypeError, arizonatransfer.getfiles, host, 3, tmp_dir)     
      self.assertException(TypeError, arizonatransfer.getfiles, host, 'a string', tmp_dir)     

      ####### test error: filelist is not a list of strings

      files = ['storkbuild.data', 3, 'string', 'd']
      self.assertException(TypeError, arizonatransfer.getfiles, host, files, tmp_dir)     

      ####### test error: some requested files don't exist, others do

      files = ['testfile', 'nonexistent_file']
      result = [tmp_dir + 'testfile']
      self.assertEqual(arizonatransfer.getfiles(host, files, tmp_dir), (False, result))
      self.__remove_files(result)

      ####### test error: destdir doesn't exist

      files = ['testfile']
      nonexistent_dir = '/tmp/directory_that_doesnt_exist'
      self.assertEqual(arizonatransfer.getfiles(host, files, nonexistent_dir), (False, []))

      ####### test error: specified transfer method doesn't exist

      original_transfermethod = arizonaconfig.get_option("transfermethod")
      arizonaconfig.set_option("transfermethod", ['nonexistenttransfermethod'])
      files = ['testfile']
      self.assertEqual(arizonatransfer.getfiles(host, files, tmp_dir), (False, []))
      arizonaconfig.set_option("transfermethod", original_transfermethod)

      ####### first specified transfer method doesn't exist but others do (should succeed)

      original_transfermethod = arizonaconfig.get_option("transfermethod")
      new_transfermethod = ['nonexistenttransfermethod']
      new_transfermethod.extend(original_transfermethod[:])
      arizonaconfig.set_option("transfermethod", new_transfermethod)
      
      files = ['testfile']
      expected_result_files = self.__get_expected_result_files(files)
      
      self.assertEqual(arizonatransfer.getfiles(host, files, tmp_dir), (True, result))
      
      self.__remove_files(expected_result_files)
      arizonaconfig.set_option("transfermethod", original_transfermethod)

      ####### end of tests. clean up.

      shutil.rmtree(tmp_dir)


      

   #------------------------------------------------------------------------------
   # sync_remote_dir(host, destdir):
   #------------------------------------------------------------------------------
   def test_sync_remote_dir(self):
      
      #TODO there is likely a way to define a method that can run after a test fails, and that
      # should be used to clean up tmp directories where files are stored. right now,
      # if a test fails then some files get left behind
      
      #TODO make sure the tarpackinfopath is cleaned up when the test is done running
      
      # make sure we start the test by downloading a new metafile
      arizonaconfig.set_option("metafilecachetime", 0)
      # TODO: decide what should be used here in the general arizonatransfer tests
      arizonaconfig.set_option("transfermethod", ['coblitz'])
      arizonaconfig.set_option("tarpackinfopath", "/tmp/stork_trans_tmp")
      
      #self.restore_stdout()
      
      host = self.host
      tmp_dir = self.tmp_dir
      
      # helpful for debugging failed tests
      #import arizonareport
      #arizonareport.set_verbosity(4)
      
      # ensure temp directory exists and is empty
      if os.path.exists(tmp_dir):
          shutil.rmtree(tmp_dir)
      os.makedirs(tmp_dir)
      
      host = host + "/sync_test6"
      
      #######  sync files between a target directory and empty directory

      # expected files must be in the same order as the files are listed in the metafile
      expected_all_files = [tmp_dir + 'stork-repository.cs.arizona.edu_packages_PlanetLab_V3_Distribution.tar.bz2',
                            tmp_dir + 'stork-repository.cs.arizona.edu_packages_PlanetLab_V3_Stable.tar.bz2', 
                            tmp_dir + 'stork-repository.cs.arizona.edu_packages_PlanetLab_V3_Unstable.tar.bz2', 
                            tmp_dir + 'stork-repository.cs.arizona.edu_packages_PlanetLab_V4_Distribution.tar.bz2', 
                            tmp_dir + 'conf.tar.bz2', 
                            tmp_dir + 'pacman.tar.bz2', 
                            tmp_dir + 'stork-repository.cs.arizona.edu_packages_PlanetLab_V3_Testing.tar.bz2', 
                            tmp_dir + 'tpfiles.tar.bz2']
      expected_grabbed_files = expected_all_files
      self.assertEqual(arizonatransfer.sync_remote_dir(host, tmp_dir), 
                       (True, expected_grabbed_files, expected_all_files))
      
      # restore metafilecachetime to speed up next tests
      #arizonaconfig.set_option("metafilecachetime", 30)

      #######  once synced no file transfer needs
      
      self.assertEqual(arizonatransfer.sync_remote_dir(host, tmp_dir), (True, [], expected_all_files))

      #######  delete one file and sync again
      
      os.unlink(expected_all_files[0])
      os.unlink(expected_all_files[0] + ".metahash")
      self.assertEqual(arizonatransfer.sync_remote_dir(host, tmp_dir), (True, expected_all_files[:1], expected_all_files))

      ####### delete several files and sync again
      
      os.unlink(expected_all_files[0])
      os.unlink(expected_all_files[0] + ".metahash")
      os.unlink(expected_all_files[1])
      os.unlink(expected_all_files[1] + ".metahash")
      os.unlink(expected_all_files[2])
      os.unlink(expected_all_files[2] + ".metahash")
      self.assertEqual(arizonatransfer.sync_remote_dir(host, tmp_dir), (True, expected_all_files[:3], expected_all_files))

      ####### if host is not a string
      
      self.assertException(TypeError, arizonatransfer.sync_remote_dir, 3, tmp_dir)

      ####### if host is incorrect
      
      wronghost = 'bogushost/keyfile'
      self.assertEqual(arizonatransfer.sync_remote_dir(wronghost, tmp_dir), (False, [], []))
      wronghost = 'quadrus.cs.arizona.edu/bogusdirectory'
      self.assertEqual(arizonatransfer.sync_remote_dir(wronghost, tmp_dir), (False, [], []))

      ####### if destdir is not a string
      
      #TODO this currently is checking the type and the exception ends up coming from something else
      # so fix this in arizonatransfer and then add this test back in
      #self.assertException(TypeError, arizonatransfer.sync_remote_dir, host, 11)

      ####### if destdir doesn't exist
      
      wrongdir = '/tmp/wrongdir'
      self.assertEqual(arizonatransfer.sync_remote_dir(host, wrongdir), (False, [], []))

      ####### if metafile is not readable
      
      testhost = self.host + '/sync_test1'
      self.assertEqual(arizonatransfer.sync_remote_dir(testhost, tmp_dir), (False, [], []))

      ####### if format of metafile is incorrect
      
      testhost =  self.host + '/sync_test2'
      # this test removed for the moment, either the test needs to be updated
      # to match current behaviour or arizonatransfer needs to be updated
      # to have the behaviour match the test
      #self.assertEqual(arizonatransfer.sync_remote_dir(testhost, tmp_dir), (False, [], []))

      ####### if metafile is empty
      
      testhost =  self.host + '/sync_test5'
      self.assertEqual(arizonatransfer.sync_remote_dir(testhost, tmp_dir), (True, [], []))
    
      ####### valid signature on signed metafile and signed by expected key
     
      testhost =  self.host + '/sync_test_valid_signed_metafile'
      expected_all_files = [tmp_dir + 'conf.tar.bz2']
      expected_grabbed_files = expected_all_files
      
      if os.path.exists(expected_all_files[0]):
          os.remove(expected_all_files[0])
      if os.path.exists(expected_all_files[0] + ".metahash"):
          os.remove(expected_all_files[0] + ".metahash")

      self.assertEqual(arizonatransfer.sync_remote_dir(testhost, tmp_dir, metafile_signature_key=self.repkey), 
                       (True, expected_grabbed_files, expected_all_files))
      
      ####### valid signature on signed metafile but not signed by expected key
    
      testhost =  self.host + '/sync_test_valid_signed_metafile'
      expected_all_files = []
      expected_grabbed_files = []
      self.assertEqual(arizonatransfer.sync_remote_dir(testhost, tmp_dir, metafile_signature_key=self.repkey2), 
                       (False, expected_grabbed_files, expected_all_files))
      
      ####### invalid signature on signed metafile
    
      testhost =  self.host + '/sync_test_invalid_signed_metafile'
      expected_all_files = []
      expected_grabbed_files = []
      self.assertEqual(arizonatransfer.sync_remote_dir(testhost, tmp_dir, metafile_signature_key=self.repkey), 
                       (False, expected_grabbed_files, expected_all_files))
    
      # cleanup
      shutil.rmtree(tmp_dir)


   #------------------------------------------------------------------------------
   # __close_transfer() :
   #------------------------------------------------------------------------------
   def test___close_transfer(self) :
      #TODO
      pass


   
   # helper function to remove files in list
   # filelist contains list of full paths to files
   def __remove_files(self, filelist):
      for i in filelist:
          if os.path.exists(i):
              os.remove(i)

   # helper function to get names of files in a directory
   def __list_all_files(self, directory):
      return_list = os.listdir(directory)
      return return_list
  
   # helper function to get expected full paths of result files
   def __get_expected_result_files(self, filelist):
      result = []
      for i in filelist:
          result.append(self.tmp_dir + i)
      return result

#=====================================================================
# Run tests
#=====================================================================
if __name__ == '__main__':
   # arizonaconfig setting for transfer
   arizonaconfig.init_options() 
   arizonaunittest.main()
