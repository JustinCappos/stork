#! /usr/bin/env python
"""
<Module>
   storktrustedpackagesTest
<Author>
   Justin Cappos
<Started>
   November 10, 2005   
<Purpose>
   Test module for stork.  See stork_nest_rpm_prepare.py for more details.
"""

import arizonaunittest
import arizonaconfig
import stork_nest_rpm_prepare
import os
import shutil

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------
   # def prepare(filename, directory):
   #------------------------------------------------------------------
   def test_prepare(self):
 
      try:
         shutil.rmtree("/tmp/foo")
      except OSError:
         pass

      
      #file does not exist
      self.assertException(TypeError, stork_nest_rpm_prepare.prepare,"/tmp/junk/wllksfdgkjlsdaklfjgldj.rpm","/tmp/foo")
      
      #not an rpm
      self.assertException(TypeError, stork_nest_rpm_prepare.prepare,"/bin/ls","/tmp/foo")
      stork_nest_rpm_prepare.prepare("/tmp/junk/mem_test-1.0.0-1.i386.rpm","/tmp/foo")
      



# Run tests
if __name__ == '__main__':
   arizonaconfig.init_options() 
   arizonaunittest.main()
