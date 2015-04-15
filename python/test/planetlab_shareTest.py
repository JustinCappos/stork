#! /usr/bin/env python
"""
<Module>
   planetlab_shareTest
<Author>
   Justin Cappos
<Started>
   December 10th, 2005   
<Purpose>
   Test module for planetlab_share.  See planetlab_share.py for more details.
"""


badclientname = "adsfkj"
clientname = "arizona_client1"
client = clientname+"@alice.cs.princeton.edu"
nestname = "arizona_stork2"
nest = nestname+"@alice.cs.princeton.edu"
nestdir = "/tmp/planetlab_shareTest_dir"


import os
import sys
import planetlab_share
import arizonaunittest
import arizonaconfig
import arizonageneral

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------
   # init_sharing_program():
   #------------------------------------------------------------------
   def test_init_sharing_program(self):

      temp_slicename = arizonaconfig.get_option("slicename")
      arizonaconfig.set_option("slicename",None)

      # Nothing set, should exit because slicename is unset
      self.assertException(SystemExit, planetlab_share.init_sharing_program)

      arizonaconfig.set_option("slicename",temp_slicename)

      planetlab_share.init_sharing_program()
      





   #------------------------------------------------------------------
   # identify(data):
   #------------------------------------------------------------------
   def test_identify(self):
      #TODO
      pass

      

      
         

   #------------------------------------------------------------------
   # identifyready(junk_data):
   #------------------------------------------------------------------
   def test_identifyready(self):
      #TODO
      pass

      

      

      
   #------------------------------------------------------------------
   # share_directory(source_slice, source_dir, target_slice, target_dir, flags):
   #------------------------------------------------------------------
   def test_share_directory(self):
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")
      try:
         # Share a dir (basic)
         arizonageneral.remote_popen(nest,"sudo sh -c 'mkdir /tmp/foo'")
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory\(\)'"),(['True'],[]))

         # check inode numbers
         inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -id /tmp/foo'")[0][0].split()[0]
         inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -id /tmp/foo2'")[0][0].split()[0]
         self.assertEquals(inode, inode2)

         # Repeated operation should have no effect
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory\(\)'"),(['True'],[]))

         # check inode numbers
         inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -id /tmp/foo'")[0][0].split()[0]
         inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -id /tmp/foo2'")[0][0].split()[0]
         self.assertEquals(inode, inode2)

         # undo the sharing...
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'"),(['True'],[]))


         # Check the read-only sharing
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory_ro\(\)'"),(['True'],[]))

         # check inode numbers
         inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -id /tmp/foo'")[0][0].split()[0]
         inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -id /tmp/foo2'")[0][0].split()[0]
         self.assertEquals(inode, inode2)
      
      
         # Make sure there was some error output
         self.assertNotEquals(arizonageneral.remote_popen(nest,"sudo sh -c 'touch /tmp/foo2/new'")[1],[])

      
         # Share with a bad client
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory_bad\(\)'"),(['False'],[]))
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory_bad_2\(\)'"),(['False'],[]))

      finally:
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo")
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo2")
         arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'")
         arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'")
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo")
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo2")
         

      


      
   #------------------------------------------------------------------
   # unshare_directory(source_slice, source_dir):
   #------------------------------------------------------------------
   def test_unshare_directory(self):
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")
      try:
         # Share a dir (nest -> nest) and unshare it
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory\(\)'"),(['True'],[]))
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'"),(['True'],[]))

         # Unshare read-only dir
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory_ro\(\)'"),(['True'],[]))
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'"),(['True'],[]))
      
         # Unshare nest-client dir
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory_c\(\)'"),(['True'],[]))
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'"),(['True'],[]))
      
         # Unshare client-nest dir
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory_c_n\(\)'"),(['True'],[]))
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'"),(['True'],[]))
      

### SEEMS TO BE A PROPER PROBLEM (can't do client to client sharing)
         # Unshare client-client dir
         #self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_share_directory_c_c\(\)'"),(['True'],[]))
         #self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'"),(['True'],[]))
      finally:
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo")
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo2")
         arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'")
         arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'")
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo")
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo2")
         

      
      
         






   #------------------------------------------------------------------
   # copy_file(source_slice,source_file, target_slice, target_file):
   #------------------------------------------------------------------
   def test_copy_file(self):
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")

      # Create and copy a file within the nest
      arizonageneral.remote_popen(nest,"sudo sh -c 'echo hello > /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_copy_file\(\)'"),(['True'],[]))

      # check inodes (should be different)
      inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertNotEquals(inode, inode2)
      # Check contents (should be same)
      data = arizonageneral.remote_popen(nest,"sudo sh -c 'cat /tmp/foo'")
      data2 = arizonageneral.remote_popen(nest,"sudo sh -c 'cat /tmp/foo2'")
      self.assertEquals(data, data2)
      

      # Should be able to do this twice with the same result (overwrite test)
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_copy_file\(\)'"),(['True'],[]))

      # check inode numbers (should be different)
      inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertNotEquals(inode, inode2)
      # Check contents (should be same)
      data = arizonageneral.remote_popen(nest,"sudo sh -c 'cat /tmp/foo'")
      data2 = arizonageneral.remote_popen(nest,"sudo sh -c 'cat /tmp/foo2'")
      self.assertEquals(data, data2)

      # Try to copy to a non-existant client
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_copy_file_bad\(\)'"),(['False'],[]))

      # Clean up
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -f /tmp/foo /tmp/foo2'")



      # nest -> client copying
      arizonageneral.remote_popen(nest,"sudo sh -c 'echo hello > /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_copy_file_c\(\)'"),(['True'],[]))

      # check inode numbers (should be different)
      inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(client,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertNotEquals(inode, inode2)
      # Check contents (should be same)
      data = arizonageneral.remote_popen(nest,"sudo sh -c 'cat /tmp/foo'")
      data2 = arizonageneral.remote_popen(client,"sudo sh -c 'cat /tmp/foo2'")
      self.assertEquals(data, data2)

      # Clean up
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -f /tmp/foo'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /tmp/foo2'")




      # client -> nest copying
      arizonageneral.remote_popen(client,"sudo sh -c 'echo hello >> /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_copy_file_c_n\(\)'"),(['True'],[]))

      # check inode numbers (should be different)
      inode = arizonageneral.remote_popen(client,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertNotEquals(inode, inode2)
      # Check contents (should be same)
      data = arizonageneral.remote_popen(client,"sudo sh -c 'cat /tmp/foo'")
      data2 = arizonageneral.remote_popen(nest,"sudo sh -c 'cat /tmp/foo2'")
      self.assertEquals(data, data2)

      # Clean up
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /tmp/foo'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -f /tmp/foo2'")



      # client -> client copying
      arizonageneral.remote_popen(client,"sudo sh -c 'echo hello >> /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_copy_file_c_c\(\)'"),(['True'],[]))

      # check inode numbers (should be different)
      inode = arizonageneral.remote_popen(client,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(client,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertNotEquals(inode, inode2)
      # Check contents (should be same)
      data = arizonageneral.remote_popen(client,"sudo sh -c 'cat /tmp/foo'")
      data2 = arizonageneral.remote_popen(client,"sudo sh -c 'cat /tmp/foo2'")
      self.assertEquals(data, data2)

      # Try to mount to a non-existant client
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_copy_file_bad_2\(\)'"),(['False'],[]))

      # Clean up
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /tmp/foo /tmp/foo2'")

      
         


   #------------------------------------------------------------------
   # link_file(source_slice, source_file, target_slice, target_file):
   #------------------------------------------------------------------
   def test_link_file(self):
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")


      # Create and link a file within the nest
      arizonageneral.remote_popen(nest,"sudo sh -c 'echo hello >> /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_link_file\(\)'"),(['True'],[]))

      # check inode numbers
      inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertEquals(inode, inode2)

      # Should be able to do this twice with the same result (overwrite test)
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_link_file\(\)'"),(['True'],[]))

      # check inode numbers
      inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertEquals(inode, inode2)

      # Try to mount to a non-existant client
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_link_file_bad\(\)'"),(['False'],[]))

      # Clean up
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -f /tmp/foo /tmp/foo2'")



      # nest -> client linking
      arizonageneral.remote_popen(nest,"sudo sh -c 'echo hello >> /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_link_file_c\(\)'"),(['True'],[]))

      # check inode numbers
      inode = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(client,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertEquals(inode, inode2)

      # Clean up
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -f /tmp/foo'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /tmp/foo2'")




      # client -> nest linking
      arizonageneral.remote_popen(client,"sudo sh -c 'echo hello >> /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_link_file_c_n\(\)'"),(['True'],[]))

      # check inode numbers
      inode = arizonageneral.remote_popen(client,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(nest,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertEquals(inode, inode2)

      # Clean up
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /tmp/foo'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -f /tmp/foo2'")



      # client -> client linking
      arizonageneral.remote_popen(client,"sudo sh -c 'echo hello >> /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_link_file_c_c\(\)'"),(['True'],[]))

      # check inode numbers
      inode = arizonageneral.remote_popen(client,"sudo sh -c 'ls -i /tmp/foo'")[0][0].split()[0]
      inode2 = arizonageneral.remote_popen(client,"sudo sh -c 'ls -i /tmp/foo2'")[0][0].split()[0]
      self.assertEquals(inode, inode2)

      # Try to mount to a non-existant client
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_link_file_bad_2\(\)'"),(['False'],[]))

      # Clean up
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /tmp/foo /tmp/foo2'")






      
         

   #------------------------------------------------------------------
   # unlink_file(target_slice, target_file):
   #------------------------------------------------------------------
   def test_unlink_file(self):
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")

      # Create and unlink a file
      arizonageneral.remote_popen(nest,"sudo sh -c 'echo hello >> /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unlink_file\(\)'"),(['True'],[]))
      # Make sure we did remove the file
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c 'ls /tmp/foo'")[0],[])

      # Unlink should fail now (file not found)
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unlink_file\(\)'"),(['False'],[]))

      # Try this for a file in the client
      arizonageneral.remote_popen(client,"sudo sh -c 'echo hello >> /tmp/foo'")
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unlink_file_c\(\)'"),(['True'],[]))
      # Make sure we did remove the file
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c 'ls /tmp/foo'")[0],[])

      # Unlink should fail now (file not found)
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unlink_file_c\(\)'"),(['False'],[]))

      # Unlink should fail (bad slice)
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unlink_file_bad\(\)'"),(['False'],[]))





   #------------------------------------------------------------------
   # protect_file(target_slice, target_file):
   #------------------------------------------------------------------
   def test_protect_file(self):
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_unshare_directory_c\(\)'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -rf /tmp/foo /tmp/foo2'")


      try:
         # Create a file
         arizonageneral.remote_popen(nest,"sudo sh -c 'echo hello > /tmp/foo'")
         # protect a file of ours
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_protect_file\(\)'"),(['True'],[]))
         # Try to append to it
         arizonageneral.remote_popen(nest,"sudo sh -c 'echo goodbye >> /tmp/foo'")
         # Check the contents
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c 'cat /tmp/foo'"),(['hello'], []))
      finally:
         arizonageneral.remote_popen(nest,"sudo sh -c 'rm -f /tmp/foo'")
         
      # Make sure we did  remove the file
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c 'ls /tmp/foo'")[0],[])
      
      # Can't protect a non-existant file
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_protect_file\(\)'"),(['False'],[]))




      try:
         # Create a file on the client
         arizonageneral.remote_popen(client,"sudo sh -c 'echo hello > /tmp/foo'")
         # protect a file of theirs
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_protect_file_c\(\)'"),(['True'],[]))
         # Try to append to it
         arizonageneral.remote_popen(client,"sudo sh -c 'echo goodbye >> /tmp/foo'")
         # Check the contents
         self.assertEquals(arizonageneral.remote_popen(client,"sudo sh -c 'cat /tmp/foo'"),(['hello'], []))
      finally:
         arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /tmp/foo'")
         
      # Make sure we did remove the file
      self.assertEquals(arizonageneral.remote_popen(client,"sudo sh -c 'ls /tmp/foo'")[0],[])
      
      # Can't protect a non-existant file
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_protect_file_c\(\)'"),(['False'],[]))


      # Try to do this for a bad client
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_protect_file_bad\(\)'"),(['False'],[]))

      








   #------------------------------------------------------------------
   # init_client(client_name):
   #------------------------------------------------------------------
   def test_init_client(self):

         
      # Try a non-existant client
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_init_client_bad\(\)'"),(['False'], []))

      # remove the share name
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /.exportdir'")

      # Try finally here so I restore the file properly if this fails
      try:
         # Should fail now
         self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_init_client\(\)'"),(['False'], []))

      finally:
         # re-set up the client
         arizonageneral.remote_popen(client,"sudo sh -c 'echo "+nestname+" > /.exportdir'")

      # Should pass now
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_init_client\(\)'"),(['True'], []))

      # Should not hurt to do this multiple times...
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_init_client\(\)'"),(['True'], []))

      # Should not hurt to do this multiple times...
      self.assertEquals(arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_init_client\(\)'"),(['True'], []))
         





   #------------------------------------------------------------------
   # share_name():
   #------------------------------------------------------------------
   def test_share_name(self):
      self.assertEquals(planetlab_share.share_name(), "planetlab")







def remote_share_directory():
   return planetlab_share.share_directory(nestname, "/tmp/foo", nestname, "/tmp/foo2","")

def remote_share_directory_ro():
   return planetlab_share.share_directory(nestname, "/tmp/foo", nestname, "/tmp/foo2","ro")

def remote_share_directory_c():
   return planetlab_share.share_directory(nestname, "/tmp/foo", clientname, "/tmp/foo2","")

def remote_share_directory_c_n():
   return planetlab_share.share_directory(clientname, "/tmp/foo", nestname, "/tmp/foo2","")

def remote_share_directory_c_c():
   return planetlab_share.share_directory(clientname, "/tmp/foo", clientname, "/tmp/foo2","")

def remote_share_directory_bad():
   return planetlab_share.share_directory(nestname, "/tmp/foo", badclientname, "/tmp/foo2","")

def remote_share_directory_bad_2():
   return planetlab_share.share_directory(badclientname, "/tmp/foo", nestname, "/tmp/foo2","")






def remote_unshare_directory():
   return planetlab_share.unshare_directory(nestname, "/tmp/foo2")

def remote_unshare_directory_c():
   return planetlab_share.unshare_directory(clientname, "/tmp/foo2")




def remote_copy_file():
   return planetlab_share.copy_file(nestname, "/tmp/foo", nestname, "/tmp/foo2")

def remote_copy_file_c():
   return planetlab_share.copy_file(nestname, "/tmp/foo", clientname, "/tmp/foo2")

def remote_copy_file_c_n():
   return planetlab_share.copy_file(clientname, "/tmp/foo", nestname, "/tmp/foo2")

def remote_copy_file_c_c():
   return planetlab_share.copy_file(clientname, "/tmp/foo", clientname, "/tmp/foo2")

def remote_copy_file_bad():
   return planetlab_share.copy_file(nestname, "/tmp/foo", badclientname, "/tmp/foo2")

def remote_copy_file_bad_2():
   return planetlab_share.copy_file(badclientname, "/tmp/foo", nestname, "/tmp/foo2")




def remote_link_file():
   return planetlab_share.link_file(nestname, "/tmp/foo", nestname, "/tmp/foo2")

def remote_link_file_c():
   return planetlab_share.link_file(nestname, "/tmp/foo", clientname, "/tmp/foo2")

def remote_link_file_c_n():
   return planetlab_share.link_file(clientname, "/tmp/foo", nestname, "/tmp/foo2")

def remote_link_file_c_c():
   return planetlab_share.link_file(clientname, "/tmp/foo", clientname, "/tmp/foo2")

def remote_link_file_bad():
   return planetlab_share.link_file(nestname, "/tmp/foo", badclientname, "/tmp/foo2")

def remote_link_file_bad_2():
   return planetlab_share.link_file(badclientname, "/tmp/foo", nestname, "/tmp/foo2")




def remote_unlink_file():
   return planetlab_share.unlink_file(nestname, "/tmp/foo")

def remote_unlink_file_c():
   return planetlab_share.unlink_file(clientname, "/tmp/foo")

def remote_unlink_file_bad():
   return planetlab_share.unlink_file(badclientname, "/tmp/foo")



def remote_protect_file():
   return planetlab_share.protect_file(nestname, "/tmp/foo")

def remote_protect_file_c():
   return planetlab_share.protect_file(clientname, "/tmp/foo")

def remote_protect_file_bad():
   return planetlab_share.protect_file(badclientname, "/tmp/foo")


def remote_init_client():
   return planetlab_share.init_client(clientname)

def remote_init_client_bad():
   return planetlab_share.init_client(badclientname)



# Run tests
if __name__=='__main__':
   # Init config options...
   args = arizonaconfig.init_options()
   arizonaconfig.set_option("slicename",nestname)

   # if we are running a test on the remote system then do it...
   if args:
      print eval(' '.join(args))
      sys.exit(0)

   try:
      # Set up the tests
      arizonageneral.remote_popen(nest,"mkdir "+nestdir)
      os.system("scp *.py "+nest+":"+nestdir)
      os.system("scp ../stork-slice "+nest+":"+nestdir)
      arizonageneral.remote_popen(client,"sudo sh -c 'echo "+nestname+" > /.exportdir'")

      # Init so the client is setup...
      arizonageneral.remote_popen(nest,"sudo sh -c '"+nestdir+"/planetlab_shareTest.py remote_init_client\(\)'")


      # Run the tests
      arizonaunittest.main()
   finally:
      # clean up the nest
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf "+nestdir+"'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo'")
      arizonageneral.remote_popen(nest,"sudo sh -c 'rm -rf /tmp/foo2'")
      # clean up the client
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -f /.exportdir'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -rf /tmp/foo'")
      arizonageneral.remote_popen(client,"sudo sh -c 'rm -rf /tmp/foo2'")
      pass

