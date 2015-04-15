#! /usr/bin/env python
"""
<Module>
   storkTest
<Author>
   Jeffry Johnston, under the direction of Justin Cappos.

   Rewritten by Collin Reynolds
   
<Started>
   October 2, 2007
<Purpose>
   Test module for stork.  See stork.py for more details.
"""

import os
import arizonaconfig
import arizonatransfer
import arizonaunittest
import stork

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   #######################################
   #   output_func_timestamp             #
   #######################################
   def test_output_func_timestamp(self):
      """STUB"""
   
   def test_increment_counter(self):
      """STUB"""
   
   def test_format_counters(self):
      """STUB"""
         
   def test_exit(self):
      """STUB"""
         
   def test_do_dumpkeys(self):
      """STUB"""   

   def test_do_list(self):
      """STUB"""
   
   def test_do_upgradeall(self):
      """STUB"""
   
   def test_do_whatrequires(self):
      """STUB"""
   
   def test_do_remove(self):
      """STUB"""
   
   def test_download_packages(self):
      """STUB"""
   
   def test_packagelog(self):
      """STUB"""
   
   def test_do_install(self):
      """STUB"""
   
   def test_wait_for_mutex(self):
      """STUB"""
   
   def test_init(self):
      """STUB"""
   
   def test_main(self):
      """STUB"""

# Run tests
if __name__ == '__main__':
   arizonaconfig.init_options("stork") 
   arizonaunittest.main()
