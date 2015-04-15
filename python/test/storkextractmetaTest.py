#! /usr/bin/env python
"""
<Module>
   storkextractmetaTest
   
<Author>
   Mario Gonzalez under the direction of Justin Cappos
   
<Started>
   June 1, 2006
   
<Purpose>
   Test module for storkextractmeta. See storkextractmeta.py for more details.
"""

import os
import arizonaconfig
import storkextractmeta
import arizonaunittest
import sys


class test(arizonaunittest.TestCase):
    
   #---------------------------------------------------------------
   # extract_metadata(files):
   #--------------------------------------------------------------
   def test_extract_metadata(self):
      # test with invalid parameters:
      self.assertException(TypeError, storkextractmeta.extract_metadata, None, None)
      self.assertException(TypeError, storkextractmeta.extract_metadata, 1, 2)
      self.assertException(TypeError, storkextractmeta.extract_metadata, {}, {})
      self.assertException(TypeError, storkextractmeta.extract_metadata, "string", ())
      
      prefix = os.environ.get("TESTPREFIX")
      args = arizonaconfig.init_options("storkextractmeta.py", alt_paths=[prefix], version="2.0")
      self.assertEquals([], args)
      self.assertEquals("/usr/local/stork/etc/stork.conf", arizonaconfig.get_option("configfile"))
       
      # I left the test with no assert or try since if it fails, the trace will print the error.
      storkextractmeta.extract_metadata([], "some destination")



# Run tests
if __name__ == '__main__':
   arizonaunittest.main()
