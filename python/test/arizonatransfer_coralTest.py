#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonatransfer_coralTest
Description:   test module for arizonatransfer_coral

Notes:
   See arizonatransfer_coral for more details.
   #Make sure that /tmp/http_test directory doesn't exist or is empty
   #before run this test.
   Modified to be more generic (for similar transfer methods, only 2 lines
   would need to be modified).
   Now ensures that the test directory is empty prior to use.
"""

import arizonatransfer_coral as transfermethod
import arizonaunittest as unittestlib
import arizonaconfig
import os

test_dir='/tmp/transfer_testdir'
transfermethod_name="arizona_coral"
test_server="stork-repository.cs.arizona.edu"

class test(unittestlib.TestCase):


   #------------------------------------------------------------------------------
   # close_transfer_program():
   #------------------------------------------------------------------------------
   def test_close_transfer_program(self):
      pass


   #------------------------------------------------------------------------------
   # init_transfer_program(uname=None,passwd=None,prt=None,ignore4=None):
   #------------------------------------------------------------------------------
   def test_init_transfer_program(self):
      pass


   #------------------------------------------------------------------------------
   # retrieve_files(host, filelist,hashlist, destdir, progress_indicator)
   #------------------------------------------------------------------------------
   def test_retrieve_files(self):
      global test_dir
      global test_server
      # basic set-up for this test      
      host = test_server+'/packages/PlanetLab/V3/Distribution/7173f45b26761e23c7bb96ff83f004e7e1bef2e7'
      # one of the files in the directory
      files = ['gnuchess-5.02-11.i386.rpm']
      # a temp directory where retrieved files will be placed
      #direc = '/tmp/http_testdir'
      # make sure temp dir is empty (errors caused during this part of the test may leave things behind)
      if os.path.exists(test_dir):
         self.__remove_files([test_dir+"/"+i for i in os.listdir(test_dir)])
      else:os.makedirs(test_dir)
      
      self.restore_stdout()      

      # retrieve one file
      result = [test_dir+"/"+files[0]]
      self.assertEqual(transfermethod.retrieve_files(host, files,[""],test_dir),(True, result))
      self.__remove_files(result)

      # retrieve several files
      files = ['gnuchess-5.02-11.i386.rpm', 'sync_file2']
      result = [test_dir+'/'+files[0]]
      self.assertEqual(transfermethod.retrieve_files(host, files,[""],test_dir),(True, result))
      self.__remove_files(result)            

      # if indicator passed in is incorret
      self.assertEqual(transfermethod.retrieve_files(host, files,[""],test_dir, 3),(False, []))
      self.assertEqual(transfermethod.retrieve_files(host, files,[""],test_dir, 'a'),(False, []))
      self.assertEqual(transfermethod.retrieve_files(host, files,[""],test_dir, unittestlib),(False, []))

      # if host is not a string
      self.assertEqual(transfermethod.retrieve_files(3, files,[""],test_dir),(False, []))      

      # if hostname is wrong
      wronghost = test_server+'/test'
      self.assertEqual(transfermethod.retrieve_files(wronghost, files, [""],test_dir),(False, []))
      wronghost = test_server+'/test/byu'
      self.assertEqual(transfermethod.retrieve_files(wronghost, files, [""],test_dir),(False, []))

      # if filelist is not a list
      self.assertEqual(transfermethod.retrieve_files(host, 'a', [""],test_dir),(False, []))      
      self.assertEqual(transfermethod.retrieve_files(host, 3, [""],test_dir),(False, []))      

      # if filelist is not a list of strings
      self.assertEqual(transfermethod.retrieve_files(host, ['a', 3, 'b'], [""],test_dir),(False, []))      
      
      # if test_dir is not a string
      self.assertEqual(transfermethod.retrieve_files(host, files, [""],3),(False, []))      

      # if test_dir does not exist
      self.assertEqual(transfermethod.retrieve_files(host, files, [""],'/no_such_dir'),(False, []))      
            
      # if try to retrieve files which don't exist
      wrongfiles = ['a']
      self.assertEqual(transfermethod.retrieve_files(host, wrongfiles, [""],test_dir),(False, []))
      wrongfiles = ['a', 'test', 'never']
      self.assertEqual(transfermethod.retrieve_files(host, wrongfiles, [""],test_dir),(False, []))


      # if try to retrieve files some of which don't exist
      wrongfiles = ['never', 'gnuchess-5.02-11.i386.rpm']
      result = [test_dir+'/gnuchess-5.02-11.i386.rpm']
      self.assertEqual(transfermethod.retrieve_files(host, wrongfiles, [""],test_dir),(True, result))
      self.__remove_files(result)
      wrongfiles = ['a', 'metafile', 'never', 'gnuchess-5.02-11.i386.rpm']
      result = [test_dir+'/gnuchess-5.02-11.i386.rpm']
      self.assertEqual(transfermethod.retrieve_files(host, wrongfiles, [""],test_dir),(True, result))
      self.__remove_files(result)

      # if try to retrieve files that a user doesn't have permission to read
      host = test_server+'/test'
      files = ['auth.py']
      self.assertEqual(transfermethod.retrieve_files(host, files, [""],test_dir),(False, []))      
      self.__remove_files(result)

      os.rmdir(test_dir)

   #------------------------------------------------------------------------------
   # transfer_name():
   #------------------------------------------------------------------------------
   def test_transfer_name(self):
      global transfermethod_name
      self.assertEqual(transfermethod.transfer_name(),transfermethod_name)
      

         

   # helper func to remove files in list
   def __remove_files(self, filelist):
      for fname in filelist:
         try:
            os.unlink(fname)
         except:
            pass

#=====================================================================
# Run tests
#=====================================================================
if __name__ == '__main__':
   unittestlib.main()
