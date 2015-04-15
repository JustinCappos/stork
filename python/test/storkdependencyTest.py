#! /usr/bin/env python
"""

<Module>
   storkdependencyTest

<Author>
   Mario Gonzalez

<Started>
   June 20, 2006

<Purpose>
   Test module for storkdependency. See storkdependency.py for more details.
"""


import os
import arizonaconfig
import arizonatransfer
import arizonaunittest
import stork
import storkdependency
import sys

class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------
   # reset_options(): resets the arizonaconfig options and reloads the
   # modules to their initial state.
   #------------------------------------------------------------------
   def reset_options(self):
       reload(storkdependency)
       reload(arizonaconfig)


   #------------------------------------------------------------------
   # this_satisfies
   #------------------------------------------------------------------
   def test_this_satisfies(self):
       self.reset_options()

       # verify correctness of package name checked
       self.assertTrue(storkdependency.this_satisfies("foo", "", "foo"))
       self.assertTrue(storkdependency.this_satisfies("foo", "", "foo = 1.2.3"))
       self.assertFalse(storkdependency.this_satisfies("foo", "", "bar"))
       self.assertFalse(storkdependency.this_satisfies("foo", "", "bar = 1.2.3"))

       # if the candidate has no version #, then always return true
       self.assertTrue(storkdependency.this_satisfies("foo", "= 1", "foo"))
       self.assertTrue(storkdependency.this_satisfies("foo", "> 1", "foo"))
       self.assertTrue(storkdependency.this_satisfies("foo", "< 1", "foo"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1", "foo"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 1", "foo"))

       # longer versions with equal prefixes are always greater
       self.assertTrue(storkdependency.this_satisfies("foo", "> 1.1", "foo = 1.1.0"))
       self.assertFalse(storkdependency.this_satisfies("foo", "= 1.1", "foo = 1.1.0"))
       self.assertFalse(storkdependency.this_satisfies("foo", "<= 1.1", "foo = 1.1.0"))

       # equal relational operators
       self.assertTrue(storkdependency.this_satisfies("foo", "= 1", "foo = 1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "= 1.1", "foo = 1.1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "= 1.1", "foo = 1.1-2"))
       # false
       self.assertFalse(storkdependency.this_satisfies("foo", "= 1", "foo = 2"))
       self.assertFalse(storkdependency.this_satisfies("foo", "= 1.1", "foo = 1.2"))

       # greater than relational operators
       self.assertTrue(storkdependency.this_satisfies("foo", "> 1", "foo = 2"))
       self.assertTrue(storkdependency.this_satisfies("foo", "> 1.1", "foo = 1.2"))
       self.assertTrue(storkdependency.this_satisfies("foo", "> 1.1", "foo = 1.2.0"))
       self.assertTrue(storkdependency.this_satisfies("foo", "> 1.1", "foo = 1.2-1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "> 1.1-1", "foo = 1.1-2"))
       #false
       self.assertFalse(storkdependency.this_satisfies("foo", "> 2", "foo = 2"))
       self.assertFalse(storkdependency.this_satisfies("foo", "> 2", "foo = 1"))
       self.assertFalse(storkdependency.this_satisfies("foo", "> 1.2", "foo = 1.1"))
       self.assertFalse(storkdependency.this_satisfies("foo", "> 1.2", "foo = 1.1-1"))
       self.assertFalse(storkdependency.this_satisfies("foo", "> 1.1-2", "foo = 1.1-1"))
       self.assertFalse(storkdependency.this_satisfies("foo", "> 1.1-2", "foo = 1.1-2"))

       # less than relational operators
       self.assertTrue(storkdependency.this_satisfies("foo", "< 2", "foo = 1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "< 1.2", "foo = 1.1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "< 1.2", "foo = 1.1.0"))
       self.assertTrue(storkdependency.this_satisfies("foo", "< 1.2", "foo = 1.1-1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "< 1.1-2", "foo = 1.1-1"))
       #false
       self.assertFalse(storkdependency.this_satisfies("foo", "< 2", "foo = 2"))
       self.assertFalse(storkdependency.this_satisfies("foo", "< 2", "foo = 3"))
       self.assertFalse(storkdependency.this_satisfies("foo", "< 1.2", "foo = 1.3"))
       self.assertFalse(storkdependency.this_satisfies("foo", "< 1.2", "foo = 1.3-1"))
       self.assertFalse(storkdependency.this_satisfies("foo", "< 1.1-2", "foo = 1.1-3"))
       self.assertFalse(storkdependency.this_satisfies("foo", "< 1.1-2", "foo = 1.1-2"))

       # greater_equal than relational operators
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1", "foo = 2"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1", "foo = 1.2"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1", "foo = 1.2.0"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1", "foo = 1.2-1"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1-1", "foo = 1.1-2"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1", "foo = 1"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1", "foo = 1.1"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1", "foo = 1.1.0"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1", "foo = 1.1-1"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1-1", "foo = 1.1-2"))
       self.assertTrue(storkdependency.this_satisfies("foo", ">= 1.1-1", "foo = 1.1-1"))
       #false
       self.assertFalse(storkdependency.this_satisfies("foo", ">= 2", "foo = 1"))
       self.assertFalse(storkdependency.this_satisfies("foo", ">= 1.2", "foo = 1.1"))
       self.assertFalse(storkdependency.this_satisfies("foo", ">= 1.2", "foo = 1.1-1"))
       self.assertFalse(storkdependency.this_satisfies("foo", ">= 1.1-2", "foo = 1.1-1"))

       # lessthan_equal than relational operators
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 2", "foo = 1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 1.2", "foo = 1.1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 1.2", "foo = 1.1.0"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 1.2", "foo = 1.1-1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 1.1-2", "foo = 1.1-1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 2", "foo = 2"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 1.2", "foo = 1.2"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 1.2", "foo = 1.2-1"))
       self.assertTrue(storkdependency.this_satisfies("foo", "<= 1.1-2", "foo = 1.1-2"))
       #false
       self.assertFalse(storkdependency.this_satisfies("foo", "<= 2", "foo = 3"))
       self.assertFalse(storkdependency.this_satisfies("foo", "<= 1.2", "foo = 1.3"))
       self.assertFalse(storkdependency.this_satisfies("foo", "<= 1.2", "foo = 1.3-1"))
       self.assertFalse(storkdependency.this_satisfies("foo", "<= 1.1-2", "foo = 1.1-3"))

   #------------------------------------------------------------------
   # find_satisfying_packages:
   #------------------------------------------------------------------
   def test_split_pack_name(self):
       self.reset_options()
       
       (name, ver, tags) = storkdependency.split_pack_name("foo>1.0-1")
       self.assertTrue(name == "foo");
       self.assertTrue(ver == ">1.0-1");

       (name, ver, tags) = storkdependency.split_pack_name("foo >1.0-1");
       self.assertTrue(name == "foo");
       self.assertTrue(ver == ">1.0-1");

       (name, ver, tags) = storkdependency.split_pack_name("foo > 1.0-1");
       self.assertTrue(name == "foo");
       self.assertTrue(ver == "> 1.0-1");

   #------------------------------------------------------------------
   # find_satisfying_packages:
   #------------------------------------------------------------------
   def test_find_satisfying_packages(self):
       pass


   #------------------------------------------------------------------
   # find_file_satisfying_packages
   #------------------------------------------------------------------
   def test_find_file_satisfying_packages(self):
       pass


   #------------------------------------------------------------------
   # find_trusted_satisfying_packages
   #------------------------------------------------------------------
   def test_find_trusted_satisfying_packages(self):
       pass


   #------------------------------------------------------------------
   # installed_satisfy
   #------------------------------------------------------------------
   def test_installed_satisfy(self):
       pass


   #------------------------------------------------------------------
   # installed_satisfy_list
   #------------------------------------------------------------------
   def test_installed_satisfy_list(self):
       pass


   #------------------------------------------------------------------
   # find_unsat_dependencies
   #------------------------------------------------------------------
   def test_find_unsat_dependencies(self):
       pass


   #------------------------------------------------------------------
   # satisfy
   #------------------------------------------------------------------
   def test_satisfy(self):
       pass



# Run tests
if __name__ == '__main__':
    arizonaunittest.main()
