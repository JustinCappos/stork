#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonatemplateTest
Description:  Test module for arizonatemplate

Notes:
See arizonatemplate for more details

"""

import arizonatemplate
import arizonaconfig
import arizonaunittest
import os
import shutil


class test(arizonaunittest.TestCase):


   #------------------------------------------------------------------
   # __divide_string_into_taglist(instring)
   #------------------------------------------------------------------
   def test_divide_string_into_taglist(self):

      # Empty string becomes list containing empty string
      self.assertEqual(arizonatemplate.divide_string_into_taglist(''),[''])
 
      # typical example
      ti = arizonaconfig.get_option('tagindicator')
      mylist = arizonatemplate.divide_string_into_taglist('abc'+ti+'def'+ti+'ghi')
      self.assertEqual(mylist[0],'abc')
      self.assertEqual(mylist[1].tagname,arizonatemplate.Tag('def').tagname)
      self.assertEqual(mylist[2],'ghi')
      
      try:
        # change the tag indicator
        arizonaconfig.set_option('tagindicator', 'A')
        mylist = arizonatemplate.divide_string_into_taglist('123A456A789')

        self.assertEqual(mylist[0],'123')
        self.assertEqual(mylist[1].tagname,arizonatemplate.Tag('456').tagname)
        self.assertEqual(mylist[2],'789')
      finally:
        # restore the indicator
        arizonaconfig.set_option('tagindicator', ti)

      # mismatched tag
      self.assertException(ValueError, arizonatemplate.divide_string_into_taglist,'start'+ti+'end')
      

      
   




   #------------------------------------------------------------------
   # retrieve_template(template_fn, tokendict={}):
   #------------------------------------------------------------------
   def test_retrieve_template(self):

      
      try:
         # set up a simple template
         template1 = "abc"
         outfo = open("template1","w")
         outfo.write(template1)
         outfo.close()

         # Do I get the same thing back without tags?
         self.assertEqual(arizonatemplate.retrieve_template("template1"),template1)
         self.assertEqual(arizonatemplate.retrieve_template("template1",{}),template1)

         # Try an example with tags
         template2 = "12###tag1###56###tag2###90"
         outfo = open("template2","w")
         outfo.write(template2)
         outfo.close()
   
         self.assertEqual(arizonatemplate.retrieve_template("template2",{'tag1':'34', 'tag2':'78'}),'1234567890')
         self.assertEqual(arizonatemplate.retrieve_template("template2",{'tag1':'-', 'tag2':'+'}),'12-56+90')
         
         # should get a IndexError because I didn't specify both tags
         self.assertException(IndexError, arizonatemplate.retrieve_template,"template1",{'tag1':'1'})



         # duplicate tags
         template3 = "###tag1###\n+\n###tag1###\n=\n###tag2###"
         outfo = open("template3","w")
         outfo.write(template3)
         outfo.close()

         self.assertEqual(arizonatemplate.retrieve_template("template3",{'tag1':'2', 'tag2':'4'}),'2\n+\n2\n=\n4')

      finally:
         # Clean up
         try:
           os.remove("template1")
         except OSError:
           pass
         try:
           os.remove("template2")
         except OSError:
           pass
         try:
           os.remove("template3")
         except OSError:
           pass


      # One last test, should be able to do this even with the file removed
      # due to caching
      self.assertEqual(arizonatemplate.retrieve_template("template3",{'tag1':'2', 'tag2':'4'}),'2\n+\n2\n=\n4')






#=====================================================================
# Run tests
#=====================================================================
if __name__=='__main__':
   arizonaconfig.init_options()
   arizonaunittest.main()
