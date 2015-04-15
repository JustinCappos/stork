#! /usr/bin/env python
"""
<Program Name>
   arizonacurlTest

<Started>
  Sept 18, 2007

<Author>
   Programmed by Collin Reynolds

<Purpose>
   Tests the arizonacurl.py program
"""

import arizonaconfig
import arizonacurl
import arizonaunittest

class test(arizonaunittest.TestCase):

   #------------------------------------
   # test_fetch_conf
   #------------------------------------
   def test_fetch_conf(self):
      self.assertTrue(arizonacurl.fetch_conf())





#=====================================================================
# Run tests
#=====================================================================
if __name__=='__main__':
   arizonaconfig.init_options()
   arizonaunittest.main()
