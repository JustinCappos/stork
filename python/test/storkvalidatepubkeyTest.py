"""
<Module>
   storkvalidatepubkeyTest

<Author>
   Collin Reynolds

<Started>
   October 23, 2007

<Purpose>
   Test module for storkvalidatepubkey.py
"""

import arizonaunittest
import arizonaconfig
import arizonareport
import os
import storkvalidatepubkey

class test(arizonaunittest.TestCase):
    
   #Test the only method in the test, which checks via arizonacrypt whether the key is valid
   def test_main(self):
      #Test with blank filename
      self.set_cmdline([""])
      self.assertException(SystemExit,storkvalidatepubkey.main)
      self.assertEquals( "error:  is not a file.", arizonareport.message)
        
      #Test a valid key generated with storkutil.py
      self.set_cmdline(["test/testkeys.publickey"])
      self.assertException(SystemExit,storkvalidatepubkey.main)
      self.assertEquals("test/testkeys.publickey is a valid public key file",arizonareport.message)
        
      #Test invalid key, some bytes deleted in a valid key
      self.set_cmdline(["test/invalid.publickey"])        
      self.assertException(SystemExit,storkvalidatepubkey.main)
      self.assertEquals("test/invalid.publickey is NOT a valid public key file",arizonareport.message)
        
      #Test invalid key, some bytes changed in valid key
      self.set_cmdline(["test/invalid2.publickey"])        
      self.assertException(SystemExit,storkvalidatepubkey.main)
      self.assertEquals("test/invalid2.publickey is NOT a valid public key file",arizonareport.message)

if __name__=='__main__':
   arizonaconfig.init_options()
   arizonaunittest.main()
