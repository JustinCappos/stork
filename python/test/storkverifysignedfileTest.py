"""
<Module>
   storkverifysignedfileTest

<Author>
   Collin Reynolds

<Started>
   October 23, 2007

<Purpose>
   Test module for storkverifysignedfile.py
"""

import arizonaunittest
import arizonaconfig
import arizonareport
import os
import storkverifysignedfile

class test(arizonaunittest.TestCase):

   #-------------------------------------------
   # main()
   #-------------------------------------------
   def test_main(self):
      pass





   #--------------------------------------------
   # move_file(src,dst)
   #--------------------------------------------		
   def test_move_file(self):
      storkverifysignedfile.move_file("test/test.txt","test/test.txt")
      self.assertException(SystemExit,storkverifysignedfile.move_file,"","")
      self.assertEqual(arizonareport.message,"dir: " + arizonaconfig.get_option("endfiledir") + " does not exist")
   
   
   
   
   #---------------------------------------------
   # verify_file(filename, path)
   #---------------------------------------------   
   def test_verify_file(self):
      #This fails for some reason
      timestamp = storkverifysignedfile.verify_file("test.txt", "test")
      self.assertEqual(timestamp,0)
      
      
      
      

if __name__=='__main__':
   arizonaconfig.init_options()
   arizonaunittest.main()
