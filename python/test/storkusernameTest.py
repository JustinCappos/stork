#! /usr/bin/env python
"""
<Module>
   storkusernameTest
<Author>
   Justin Cappos
<Started>
   November 7th, 2005   
<Purpose>
   Test module for storkusername.  See storkusername.py for more details.
"""




import os
import storkusername
import arizonaunittest
import arizonaconfig
import arizonacrypt

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------
   # config_prefix()
   #------------------------------------------------------------------
   def test_config_prefix(self):

      # Init config options...
      arizonaconfig.init_options()

      # Get a valid publickey file
      priv_sl = arizonacrypt.generate_privatekey_sl()
      pubkey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_sl(priv_sl)
      publickey_fn = arizonacrypt.sl_to_fn(pubkey_sl)

      # Since I don't know the publickey, I assume this is okay if 
      # config_prefix() doesn't throw an exception
      arizonaconfig.set_option("username","abc")
      arizonaconfig.set_option("publickeyfile",publickey_fn)
      storkusername.config_prefix()

      # make sure that the embedded name is used if all are set.
      arizonaconfig.set_option("embeddedusername","abc123")
      #This is now hashed
      #self.assertEquals(storkusername.config_prefix(),"abc123")

      # unset options
      arizonaconfig.set_option("username","")
      arizonaconfig.set_option("publickeyfile","")
      arizonaconfig.set_option("embeddedusername","")
      
      # Nothing set, should throw TypeError
      self.assertException(TypeError, storkusername.config_prefix())

      # Only username, should throw TypeError
      arizonaconfig.set_option("username","abc")
      self.assertException(TypeError, storkusername.config_prefix())

      # Only publickeyfile, should throw TypeError
      arizonaconfig.set_option("username","")
      arizonaconfig.set_option("publickeyfile",publickey_fn)
      self.assertException(TypeError, storkusername.config_prefix())

      # Invalid publickeyfile, should throw TypeError
      arizonaconfig.set_option("username","abc")
      arizonaconfig.set_option("publickeyfile","/bin/ls")
      self.assertException(TypeError, storkusername.config_prefix())

      # Missing publickeyfile, should throw TypeError
      arizonaconfig.set_option("username","abc")
      arizonaconfig.set_option("publickeyfile","/ajldf/asflas")
      self.assertException(TypeError, storkusername.config_prefix())

      os.remove(publickey_fn)


      
      
         







# Run tests
if __name__=='__main__':
   arizonaunittest.main()
