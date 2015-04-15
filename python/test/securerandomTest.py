#! /usr/bin/env python
"""
<Module>
   securerandomTest
<Author>
   Collin Reynolds
<Started>
   Nov 5, 2007
<Purpose>
   Test module for securerandom, see securerandom.py for more details.
"""

import securerandom
import arizonaunittest

class test(arizonaunittest.TestCase):
   
   #-------------------------
   # seed(self, junk)
   #-------------------------
   def test_seed(self):
      pass




   #-------------------------
   # getstate(self)
   #-------------------------
   def test_getstate(self):
      pass




   #-------------------------
   # setstate(self, junk)
   #-------------------------
   def test_setstate(self):
      pass
  
  
   
   
   #-------------------------
   # jumpahead(self, junk)
   #-------------------------
   def test_jumpahead(self):
      pass



   #-------------------------
   # random(self)
   #-------------------------
   def test_random(self):
      rand = securerandom.SecureRandom()
      #Make sure it returns the right type
      self.assertEqual(type(rand.random()),type(.002))
      #Make sure it doesn't generate the same number twice
      self.assertFalse(rand.random() == rand.random())
      self.assertFalse(rand.random() == rand.random())
  
  
  
  
# Run tests
if __name__=='__main__':
   arizonaunittest.main()