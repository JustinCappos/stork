#! /bin/env/python

"""
<Module>
   arizonagroupTest

<Author>
   Michael White

<Started>
   October 14, 2007

<Purpose>
   Unit tests for arizonagroup.py
"""

import arizonaunittest
import arizonagroup
import pacman

class test(arizonaunittest.TestCase):
   
   def test_groupunion(self):
      #Test groups with no overlap
      smallNums = arizonagroup.groupunion('smallNums', ['evens', 2,4,6,8,10], ['odds', 1,3,5,7,9])
      expectedValue = ['smallNums' ,2,4,6,8,10,1,3,5,7,9]
      self.assertEqual(smallNums, expectedValue)


      #Test groups that are equal
      self.assertEqual(arizonagroup.groupunion('newGroup', ['group1', 'a','b','c','d'], ['group1', 'a','b','c','d']), ['newGroup', 'a','b','c','d'])

      #Test groups with some overlap
      self.assertEqual(arizonagroup.groupunion('unioned group', ['first group', 'first', 'second', 'fifth'], ['second group', 'first', 'third', 'fourth', 'fifth']), ['unioned group', 'first', 'second', 'fifth', 'third', 'fourth'])

      #Test empty groups
      self.assertEqual(arizonagroup.groupunion('same group', ['group1', '1', 'a', '2'], ['emptygroup']), ['same group', '1', 'a', '2'])
      self.assertEqual(arizonagroup.groupunion('same group', ['group1', '1', 'a', '2'], []), ['same group', '1', 'a', '2'])
      
      
      


   def test_groupintersect(self):
   
      #Test groups with no overlap
      self.assertEqual(arizonagroup.groupintersect('nothing', ['evens', 2, 4, 6, 8, 10], ['odds', 1,3,5,7,9]), ['nothing'])
     
      #Test groups that are equal
      self.assertEqual(arizonagroup.groupintersect('same group', ['group a', 'a', 1, 'b', 2], ['group b' , 'a', 1, 'b', 2]), ['same group', 'a', 1, 'b', 2])
     
      #Test groups with some overlap
      self.assertEqual(arizonagroup.groupintersect('intersected group', ['first group', 1, 2, 4, 5], ['second group', 1, 3, 5, 6, 7]), ['intersected group', 1, 5])
     
      #Test empty groups
      self.assertEqual(arizonagroup.groupintersect('empty group', ['empty'], ['not empty', 1, 5, 6] ), ['empty group'])
      self.assertEqual(arizonagroup.groupintersect('empty group', ['not empty', 1, 5, 6], ['empty'] ), ['empty group'])





   def test_groupexclude(self):
      #Test exclusion when group contains elements to be excluded
      A = ['group', 1, 2, 3, 4, 5, 6, 7, 8]
      arizonagroup.groupexclude(A , [2, 4, 7]), 
      self.assertEqual(A, ['group', 1,3,5,6,8])

      #Test exclusion when group does not contain elements to be excluded
      A = ['group1', 1, 2, 3, 4, 'juice']
      arizonagroup.groupexclude(A , [57, 52, 'orange', 'HUGE GUTS'])
      self.assertEqual(A, ['group1', 1, 2, 3, 4, 'juice'])





	
   def test_groupcomplement(self):
      #Test exclusion when group contains elements to be excluded
      self.assertEqual(arizonagroup.groupcomplement('newGroup' ,['group', 1,2,3,4,5,6,7,8] , ['subgroup', 2, 4, 7]), ['newGroup', 1,3,5,6,8])

      #Test exclusion when group does not contain elements to be excluded
      self.assertEqual(arizonagroup.groupcomplement('group2', ['group1', 1, 2, 3, 4, 'juice'], ['not a subgroup', 57, 52, 'orange', 'HUGE GUTS']), ['group2', 1, 2, 3, 4, 'juice'])
      
      self.assertEqual(arizonagroup.groupcomplement('group2', ['group1', 1, 2, 3, 4, 'juice'], ['partial', 2, 4, 58, 'DERP']), ['group2', 1, 3, 'juice'])






   def test_groupsubtract(self):
      #Test subtract when B is a subset of A
      A = ['group A', 1, 2, 3, 4, 5, 6]
      B = ['group B', 2, 4, 6]
      arizonagroup.groupsubtract(A, B)
      self.assertEqual(A, ['group A', 1, 3, 5])

      #Test subtract when B intersect A is empty 
      A = ['group A', 1, 2, 3, 4, 5, 6]
      B = ['group B', 'apples', 'bananas', 'oranges', 'grapes']
      arizonagroup.groupsubtract(A, B)
      self.assertEqual(A, ['group A', 1, 2, 3, 4, 5, 6])

      #Test subtract when A intersect B is non-empty, but B is not a subset of A
      A = ['group A', 1, 2, 3, 4, 5, 6]
      B = ['group B', 2, 'love', 3, 'kittens', 4, 'cake']
      arizonagroup.groupsubtract(A, B)
      self.assertEqual(A, ['group A', 1, 5, 6])




   olddict = pacman.GroupFileParse("groups.dtd", "white.groups.pacman")
   newdict = arizonagroupparse.GroupFileParse("groups.dtd", "white.groups.pacman")

   #Test file parsing methods
   def test_include(self):
      self.assertEqual(olddict["includegroup1"], newdict["includegroup1"])
      self.assertEqual(olddict["includegroup2"], newdict["includegroup2"])
      self.assertEqual(olddict["includegroup3"], newdict["includegroup3"])
      self.assertEqual(olddict["includegroup4"], newdict["includegroup4"])






   def test_exclude(self):
      self.assertEqual(olddict["excludegroup1"], newdict["excludegroup1"])
      self.assertEqual(olddict["excludegroup2"], newdict["excludegroup2"])
      self.assertEqual(olddict["excludegroup3"], newdict["excludegroup3"])
      self.assertEqual(olddict["excludegroup4"], newdict["excludegroup4"])






   def test_intersect(self):
      self.assertEqual(olddict["intersectgroup1"], newdict["intersectgroup1"])
      self.assertEqual(olddict["intersectgroup2"], newdict["intersectgroup2"])
      self.assertEqual(olddict["intersectgroup3"], newdict["intersectgroup3"])
      self.assertEqual(olddict["intersectgroup4"], newdict["intersectgroup4"])








if __name__ == "__main__":
    arizonaunittest.main()
