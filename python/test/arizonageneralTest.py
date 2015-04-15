#! /usr/bin/env python
"""
<Module>
   arizonageneralTest
<Author>
   Jeffry Johnston, under the direction of Justin Cappos
<Started>
   August 13, 2005   
<Purpose>
   Test module for arizonageneral.  See arizonageneral.py for more details.
"""




import os
import shutil
import arizonageneral
import arizonaunittest

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------
   # uniq(orig_list)
   #------------------------------------------------------------------
   def test_uniq(self):
      self.assertException(TypeError, arizonageneral.uniq, list)
      self.assertException(TypeError, arizonageneral.uniq, 123)
      self.assertEqual(arizonageneral.uniq(None), [])
      self.assertEqual(arizonageneral.uniq(""), [])
      self.assertEqual(arizonageneral.uniq([]), [])
      self.assertEqual(arizonageneral.uniq([[]]), [[]])
      self.assertEqual(arizonageneral.uniq((int,int)), [int])
      self.assertEqual(arizonageneral.uniq(["a","a","a"]), ["a"])
      self.assertEqual(arizonageneral.uniq(["a","b","a"]), ["a", "b"])
      self.assertEqual(arizonageneral.uniq(["b","a","a"]), ["b", "a"])
      self.assertEqual(arizonageneral.uniq(["a","a","b"]), ["a", "b"])
      self.assertEqual(arizonageneral.uniq([1,1.0,"1"]), [1, "1"])
      self.assertEqual(arizonageneral.uniq("\r \r \t \t \n \n"), ["\r", " ", "\t", "\n"])
      
      
      
      


   #------------------------------------------------------------------
   # intersect(list_a,list_b)
   #------------------------------------------------------------------
   def test_intersect(self):   
      self.assertException(TypeError, arizonageneral.intersect,"3")
      self.assertException(TypeError, arizonageneral.intersect,.5,.5)
      self.assertException(TypeError, arizonageneral.intersect,"",5)
      self.assertException(TypeError, arizonageneral.intersect,0,"t")
      self.assertException(TypeError, arizonageneral.intersect,356345,[])
      self.assertException(TypeError, arizonageneral.intersect,[],.5645)
      self.assertEqual(arizonageneral.intersect(["a","b","c"],["c","d","e"]),["c"])
      self.assertEqual(arizonageneral.intersect([1,3,5,6,7],[1,3,7]),[1,3,7])
      
      
      
      
      
   #------------------------------------------------------------------
   # subtract(list_a,list_b)
   #------------------------------------------------------------------
   def test_subtract(self):   
      self.assertException(TypeError, arizonageneral.subtract,"3")
      self.assertException(TypeError, arizonageneral.subtract,.5,.5)
      self.assertException(TypeError, arizonageneral.subtract,"",5)
      self.assertException(TypeError, arizonageneral.subtract,0,"t")
      self.assertException(TypeError, arizonageneral.subtract,356345,[])
      self.assertException(TypeError, arizonageneral.subtract,[],.5645)
      self.assertEqual(arizonageneral.subtract(["a","b","c"],["c","d","e"]),["a","b"])
      self.assertEqual(arizonageneral.subtract([1,3,5,6,7],[1,3,7]),[5,6])
      
      
      
      
            
   #------------------------------------------------------------------
   # recur_depth(func_name)
   #------------------------------------------------------------------
   def recur_test(self, level):
      self.assertEqual(arizonageneral.recur_depth("recur_test"), 6 - level)
      if level > 0:
         self.recur_test(level - 1)

   def test_recur_depth(self):
      # check bad params
      self.assertException(TypeError, arizonageneral.recur_depth, 1)
      self.assertException(TypeError, arizonageneral.recur_depth, self)
      
      # test non-existent function
      self.assertEqual(arizonageneral.recur_depth("a"), 0)
      
      # test this function (depth should be 1)
      self.assertEqual(arizonageneral.recur_depth("test_recur_depth"), 1)
      
      # recursive check
      self.recur_test(5)

         



   #------------------------------------------------------------------
   # format_list(string_list, separator, head, headnew, tail)
   #------------------------------------------------------------------
   def test_format_list(self):
      # test missing params, header/footer
      self.assertEqual(arizonageneral.format_list([], None, None, None, None), '')
      self.assertEqual(arizonageneral.format_list([], None, "abc", None, None), 'abc')
      self.assertEqual(arizonageneral.format_list([], None, None, None, "def"), 'def')
      self.assertEqual(arizonageneral.format_list([], None, "abc", None, "def"), 'abcdef')
      self.assertEqual(arizonageneral.format_list(["g", "h\n", "i"], None, "abc", None, "def"), 'abcgh\nidef')

      # test line wrapping      
      self.assertEqual(arizonageneral.format_list(["0000000000", "1111111111", 
          "2222222222", "3333333333", "4444444444", "5555555555", 
          "6666666666", "7777777777", "8"], None, None, None, None), 
          '00000000001111111111222222222233333333334444444444555555555566666666667777777777\n8')
      self.assertEqual(arizonageneral.format_list(["0000000000", "1111111111", 
          "2222222222", "3333333333", "4444444444", "5555555555", 
          "6666666666", "777777777", "8"], None, None, None, None), 
          '00000000001111111111222222222233333333334444444444555555555566666666667777777778')
          
      # test separator    
      self.assertEqual(arizonageneral.format_list(["000000000", "111111111", 
          "222222222", "333333333", "444444444", "555555555", 
          "666666666", "7777777777"], ",", None, None, None), 
          '000000000,111111111,222222222,333333333,444444444,555555555,666666666,7777777777')
      self.assertEqual(arizonageneral.format_list(["000000000", "111111111", 
          "222222222", "333333333", "444444444", "555555555", 
          "666666666", "7777777777"], ",", None, None, None), 
          '000000000,111111111,222222222,333333333,444444444,555555555,666666666,7777777777')
      self.assertEqual(arizonageneral.format_list(["00000000", "11111111", 
          "22222222", "33333333", "44444444", "55555555", 
          "66666666", "7777777", "8"], "__", None, None, None), 
          '00000000__11111111__22222222__33333333__44444444__55555555__66666666__7777777__8')
      self.assertEqual(arizonageneral.format_list(["00000000", "11111111", 
          "22222222", "33333333", "44444444", "55555555", 
          "66666666", "7777777", "8"], "__", "a", "b", "c"), 
          'a00000000__11111111__22222222__33333333__44444444__55555555__66666666__7777777__\nb8c')





   #------------------------------------------------------------------
   # system_timeout(command, tries, wait, kill_signal)
   #------------------------------------------------------------------
   def test_system_timeout(self):
       
      # should raise an exception when parameters passed are not the expected ones:
      self.assertException(TypeError, arizonageneral.system_timeout, 23, 23, 23, 23)
      self.assertException(TypeError, arizonageneral.system_timeout, (23, 23, 23, 23))
      self.assertException(TypeError, arizonageneral.system_timeout, "", {}, 23, 23)
      self.assertException(TypeError, arizonageneral.system_timeout, "", 23, [], 23)
      self.assertException(TypeError, arizonageneral.system_timeout, "", 23, 23, "str")
      self.assertException(TypeError, arizonageneral.system_timeout, [], [], [], [])
      self.assertException(TypeError, arizonageneral.system_timeout, ("", {}, 23, 23) )
      self.assertException(TypeError, arizonageneral.system_timeout, ("", 23, [], 23) )
      self.assertException(TypeError, arizonageneral.system_timeout, ("", 23, 23, "str") )
      self.assertException(TypeError, arizonageneral.system_timeout, ([], [], [], []) )
      self.assertException(TypeError, arizonageneral.system_timeout, ["", {}, 23, 23] )
      self.assertException(TypeError, arizonageneral.system_timeout, ["", 23, [], 23] )
      self.assertException(TypeError, arizonageneral.system_timeout, ["", 23, 23, "str"] )
      self.assertException(TypeError, arizonageneral.system_timeout, [[], [], [], []] )
      
      self.assertRaises( TypeError, arizonageneral.system_timeout, "", 2.3, 2, 3 )
      self.assertRaises( TypeError, arizonageneral.system_timeout, "", 2, 2.5, 3 )
      self.assertRaises( TypeError, arizonageneral.system_timeout, "", 2, 2, 3.5 )
      self.assertRaises( TypeError, arizonageneral.system_timeout, "", 2.3, 2.5, 3.32 )
      
      # should return (False, 0) when the second and third arguments are 0 (zero):
      self.assertEquals( (False, 0),  arizonageneral.system_timeout("", 0, 0, 0) )
      self.assertEquals( (False, 0),  arizonageneral.system_timeout("", 0, 2, 0) )
      self.assertEquals( (False, 0),  arizonageneral.system_timeout("", 1, 0, 0) )
      
      # should raise an exception when a negative integer is passed for the second and third arguments:
      self.assertRaises(ValueError, arizonageneral.system_timeout, "", -1, 1, 0 )
      self.assertRaises(ValueError, arizonageneral.system_timeout, "", 10, -1, 0 )
      self.assertRaises(ValueError, arizonageneral.system_timeout, "", -100, 100, 0 )
      self.assertRaises(ValueError, arizonageneral.system_timeout, "", 10, -100, 0 )
      self.assertRaises(ValueError, arizonageneral.system_timeout, "", -1, -1, 0 )


      # TODO: test with normal input





   #------------------------------------------------------------------
   # system_timeout(command, tries, wait, kill_signal=15)
   #------------------------------------------------------------------
   def test_system_timeout_backoff(self):   
       # should raise an exception when parameters passed are not the expected ones:
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, 23, 23, 23, 23)
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, (23, 23, 23, 23))
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, "", {}, 23, 23)
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, "", 23, [], 23)
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, "", 23, 23, "str")
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, [], [], [], [])
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, ("", {}, 23, 23) )
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, ("", 23, [], 23) )
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, ("", 23, 23, "str") )
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, ([], [], [], []) )
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, ["", {}, 23, 23] )
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, ["", 23, [], 23] )
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, ["", 23, 23, "str"] )
      self.assertException(TypeError, arizonageneral.system_timeout_backoff, [[], [], [], []] )
      
      self.assertRaises( TypeError, arizonageneral.system_timeout_backoff, "", 2.3, 2, 3 )
      self.assertRaises( TypeError, arizonageneral.system_timeout_backoff, "", 2, 2.5, 3 )
      self.assertRaises( TypeError, arizonageneral.system_timeout_backoff, "", 2, 2, 3.5 )
      self.assertRaises( TypeError, arizonageneral.system_timeout_backoff, "", 2.3, 2.5, 3.32 )
      
      # should return (False, 0) when the second and third arguments are 0 (zero):
      self.assertEquals( (False, 0),  arizonageneral.system_timeout("", 0, 0, 0) )
      self.assertEquals( (False, 0),  arizonageneral.system_timeout("", 0, 2, 0) )
      self.assertEquals( (False, 0),  arizonageneral.system_timeout("", 1, 0, 0) )
      
      # should raise an exception when a negative integer is passed for the second and third arguments:
      self.assertRaises(ValueError, arizonageneral.system_timeout_backoff, "", -1, 1, 0 )
      self.assertRaises(ValueError, arizonageneral.system_timeout_backoff, "", 10, -1, 0 )
      self.assertRaises(ValueError, arizonageneral.system_timeout_backoff, "", -100, 100, 0 )
      self.assertRaises(ValueError, arizonageneral.system_timeout_backoff, "", 10, -100, 0 )
      self.assertRaises(ValueError, arizonageneral.system_timeout_backoff, "", -1, -1, 0 )


      # TODO: test with normal input
   
   
   
   
   
   
   #------------------------------------------------------------------
   # system2(command)
   #------------------------------------------------------------------
   def test_system2(self):
      self.assertException(TypeError, arizonageneral.system2, 1)
      # TODO figure out how to test
      #open("/tmp/test", "w") 
      #arizonageneral.system2('/bin/echo "test" > /tmp/test')




   
   #------------------------------------------------------------------
   # fsystem2(comm, command)
   #------------------------------------------------------------------
   def test_fsystem2(self):
      self.assertException(TypeError, arizonageneral.fsystem2, 1, 1)
      self.assertException(TypeError, arizonageneral.fsystem2, "", 1)
      self.assertException(TypeError, arizonageneral.fsystem2, 1, "")
      # TODO figure out how to test
      
      
      
      
      
   #------------------------------------------------------------------
   # popen0(cmd)
   #------------------------------------------------------------------
   def test_popen0(self):
      pass #figure out how to test





   #------------------------------------------------------------------
   # popen5(cmd)
   #------------------------------------------------------------------
   def test_popen5(self):
      self.assertException(TypeError, arizonageneral.popen5, 1)
      # TODO figure out how to test
      
      
      
      
   #------------------------------------------------------------------
   # popen6(cmd)
   #------------------------------------------------------------------
   def test_popen6(self):
      pass #Figure out how to test




      
   #------------------------------------------------------------------
   # split_quoted(text)
   #------------------------------------------------------------------
   def test_split_quoted(self):
      self.assertException(TypeError, arizonageneral.split_quoted, 1)
      self.assertException(TypeError, arizonageneral.split_quoted, None)
      self.assertEqual(arizonageneral.split_quoted(''), [])
      self.assertEqual(arizonageneral.split_quoted('abcd'), ['abcd'])
      self.assertEqual(arizonageneral.split_quoted('"abcd"'), ['abcd'])
      self.assertEqual(arizonageneral.split_quoted('ab cd'), ['ab', 'cd'])
      self.assertEqual(arizonageneral.split_quoted('"ab cd"'), ['ab cd'])
      self.assertEqual(arizonageneral.split_quoted('"ab " cd"ef"'), ['ab ', 'cd', 'ef'])
      self.assertEqual(arizonageneral.split_quoted('"ab " cd"ef'), ['ab ', 'cd', 'ef'])
      self.assertEqual(arizonageneral.split_quoted('"ab cd ef'), ['ab cd ef'])
      self.assertEqual(arizonageneral.split_quoted('a      b"c d e f'), ['a', 'b', 'c d e f'])
      self.assertEqual(arizonageneral.split_quoted('   "a    b"   '), ['a    b'])




   
   #------------------------------------------------------------------
   # check_type(variable, parameter_name, expected_type, function_name)
   #------------------------------------------------------------------
   def test_check_type(self):
      # check params
      self.assertException(TypeError, arizonageneral.check_type, "a", "b", "c", "d")
      self.assertException(TypeError, arizonageneral.check_type, None, None, None, "d")
      self.assertException(TypeError, arizonageneral.check_type, None, "b", None, None)
      self.assertException(TypeError, arizonageneral.check_type, None, "b", 4, "d")
      
      # check None
      arizonageneral.check_type(None, "b", None, "d")
      self.assertException(TypeError, arizonageneral.check_type, "a", "b", None, "d")

      # check "iterable"
      self.assertException(TypeError, arizonageneral.check_type, None, "b", "iterable", "d")
      self.assertException(TypeError, arizonageneral.check_type, 1, "b", "iterable", "d")
      arizonageneral.check_type([], "b", "iterable", "d")
      arizonageneral.check_type([1], "b", "iterable", "d")
      arizonageneral.check_type({"a":"b", "c":"d"}, "b", "iterable", "d")
      arizonageneral.check_type("abc", "b", "iterable", "d")
      file_in = open("/dev/null")
      arizonageneral.check_type(file_in, "b", "iterable", "d")
      file_in.close()

      # check lists
      self.assertException(TypeError, arizonageneral.check_type, 1, "b", [[tuple, "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_type, [], "b", [[list, "any"]], "d")
      arizonageneral.check_type([1, 2], "b", [[list, "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_type, (1, 2), "b", [[list, "any"]], "d")
      arizonageneral.check_type(["a", "b"], "b", [[list, str]], "d")
      self.assertException(TypeError, arizonageneral.check_type, [1, 2], "b", [[list, str]], "d")

      # check "iterable" as the first item of a list
      self.assertException(TypeError, arizonageneral.check_type, 1, "b", [["iterable", "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_type, [], "b", [["iterable", "any"]], "d")
 
      # check "any"
      arizonageneral.check_type(None, "b", "any", "d")
      arizonageneral.check_type("a", "b", "any", "d")
      arizonageneral.check_type("a", "b", [int, "any"], "d")
      arizonageneral.check_type("a", "b", ["any", int], "d")
      arizonageneral.check_type(self, "b", "any", "d")
      arizonageneral.check_type(([1, -5.4], int, None, ), "b", "any", "d")
      self.assertException(TypeError, arizonageneral.check_type, 1, "b", [[list, 'any']], "d")
      arizonageneral.check_type([1], "b", [[list, 'any']], "d")

      # check "parent"
      arizonageneral.check_type(None, "b", "parent", "d")
      arizonageneral.check_type(1, "b", [int, [list, "parent"]], "d")
      arizonageneral.check_type([1, 2], "b", [int, [list, "parent"]], "d")
      arizonageneral.check_type([1, [2, [[[3]]]], 4], "b", [int, [list, "parent"]], "d")
      self.assertException(TypeError, arizonageneral.check_type, [1, [2, [[["a"]]]], 4], "b", [int, [list, "parent"]], "d")

      # check "empty"
      arizonageneral.check_type([], "b", [[list, str, "empty"]], "d")
      arizonageneral.check_type(["a", "b"], "b", [[list, str, "empty"]], "d")
      
      
      
      
   #------------------------------------------------------------------
   # check_types(list, function, modulename=None)
   #------------------------------------------------------------------
   def test_check_types(self):
      
      # check None
      self.assertException(TypeError, arizonageneral.check_types,None, "d")
      self.assertException(TypeError, arizonageneral.check_types, [["a", None]], "d")

      # check "iterable"
      self.assertException(TypeError, arizonageneral.check_types, [["b", "iterable"]], "d")
      self.assertException(TypeError, arizonageneral.check_types, [[1, "iterable"]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[[], "iterable"]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[[1], "iterable"]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[{"a":"b", "c":"d"}, "iterable"]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[["abc", "iterable"]], "d")
      file_in = open("/dev/null")
      self.assertException(TypeError, arizonageneral.check_types,[[file_in, "iterable"]], "d")
      file_in.close()

      # check lists
      self.assertException(TypeError, arizonageneral.check_types, [[1, [[tuple, "any"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types, [[[], [[list, "any"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[[1, 2], [[list, "any"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types, [[(1, 2), [[list, "any"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[["a", "b"], [[list, str]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types, [[[1, 2], [[list, str]]]], "d")

      # check "iterable" as the first item of a list
      self.assertException(TypeError, arizonageneral.check_types, [[1, [["iterable", "any"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types, [[[],  [["iterable", "any"]]]], "d")
 
      # check "any"
      self.assertException(TypeError, arizonageneral.check_types,[[None, "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[["a", "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[["a", [int, "any"]]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[["a",  ["any", int]]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[self, "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[([1, -5.4], int, None, ), "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_types, [[1,[[list, 'any']]]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[[1], [[list, 'any']]]], "d")

      # check "parent"
      self.assertException(TypeError, arizonageneral.check_types,[[None, "parent"]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[1, [int, [list, "parent"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[[1, 2], [int, [list, "parent"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[[1, [2, [[[3]]]], 4], [int, [list, "parent"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types, [[[1, [2, [[["a"]]]], 4], [int, [list, "parent"]]]], "d")

      # check "empty"
      self.assertException(TypeError, arizonageneral.check_types,[[[], [[list, str, "empty"]]]], "d")
      self.assertException(TypeError, arizonageneral.check_types,[[["a", "b"], [[list, str, "empty"]]]], "d")
   	
   	
   	
   	
   #------------------------------------------------------------------
   # check_type_simple(variable, parameter_name, expected_type, function_name, noneok=False)
   #------------------------------------------------------------------
   def test_check_type_simple(self):
      # check params
      self.assertException(TypeError, arizonageneral.check_type_simple, "a", "b", "c", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, None, None, None, "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, None, "b", None, None)
      self.assertException(TypeError, arizonageneral.check_type_simple, None, "b", 4, "d")
      
      # check None
      self.assertException(TypeError, arizonageneral.check_type_simple,None, "b", None, "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, "a", "b", None, "d")

      # check "iterable"
      self.assertException(TypeError, arizonageneral.check_type_simple, None, "b", "iterable", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, 1, "b", "iterable", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,[], "b", "iterable", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,[1], "b", "iterable", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,{"a":"b", "c":"d"}, "b", "iterable", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,"abc", "b", "iterable", "d")
      file_in = open("/dev/null")
      self.assertException(TypeError, arizonageneral.check_type_simple,file_in, "b", "iterable", "d")
      file_in.close()

      # check lists
      self.assertException(TypeError, arizonageneral.check_type_simple, 1, "b", [[tuple, "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, [], "b", [[list, "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,[1, 2], "b", [[list, "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, (1, 2), "b", [[list, "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,["a", "b"], "b", [[list, str]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, [1, 2], "b", [[list, str]], "d")

      # check "iterable" as the first item of a list
      self.assertException(TypeError, arizonageneral.check_type_simple, 1, "b", [["iterable", "any"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, [], "b", [["iterable", "any"]], "d")
 
      # check "any"
      self.assertException(TypeError, arizonageneral.check_type_simple,None, "b", "any", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,"a", "b", "any", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,"a", "b", [int, "any"], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,"a", "b", ["any", int], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,self, "b", "any", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,([1, -5.4], int, None, ), "b", "any", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, 1, "b", [[list, 'any']], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,[1], "b", [[list, 'any']], "d")

      # check "parent"
      self.assertException(TypeError, arizonageneral.check_type_simple,None, "b", "parent", "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,1, "b", [int, [list, "parent"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,[1, 2], "b", [int, [list, "parent"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,[1, [2, [[[3]]]], 4], "b", [int, [list, "parent"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple, [1, [2, [[["a"]]]], 4], "b", [int, [list, "parent"]], "d")

      # check "empty"
      self.assertException(TypeError, arizonageneral.check_type_simple,[], "b", [[list, str, "empty"]], "d")
      self.assertException(TypeError, arizonageneral.check_type_simple,["a", "b"], "b", [[list, str, "empty"]], "d")
      
      # check correct input
      arizonageneral.check_type_simple("test","test",str,"test")
      arizonageneral.check_type_simple(["test"],"test",list,"test")
      arizonageneral.check_type_simple(1,"test",int,"test")
      arizonageneral.check_type_simple({},"test",dict,"test")
      arizonageneral.check_type_simple(None,"test",list,"test",noneok=True)
   	
   




   #------------------------------------------------------------------
   # check_type_stringlist(variable, parameter_name, function_name)
   #------------------------------------------------------------------
   def test_check_type_stringlist(self):
   
      #Check normal input
      arizonageneral.check_type_stringlist([], "test", "test")
      arizonageneral.check_type_stringlist([""], "test", "test")
      arizonageneral.check_type_stringlist(["",""], "test", "test")
      arizonageneral.check_type_stringlist(["","56","hello"], "test", "test")
      arizonageneral.check_type_stringlist(["test","test","","",""], "test", "test")
      
      #Check bad input
      self.assertException(TypeError, arizonageneral.check_type_stringlist,"", "test", "test")
      self.assertException(TypeError, arizonageneral.check_type_stringlist,[1,2,3], "test", "test")
      self.assertException(TypeError, arizonageneral.check_type_stringlist,{}, "test", "test")
      self.assertException(TypeError, arizonageneral.check_type_stringlist,[1,5,"",34], "test", "test")
      self.assertException(TypeError, arizonageneral.check_type_stringlist,[{}], "test", "test")   	
      self.assertException(TypeError, arizonageneral.check_type_stringlist,None, "test", "test")   	
      
   	
   	
   	
   	

   #------------------------------------------------------------------
   # make_daemon(program)
   #------------------------------------------------------------------
   def test_make_daemon(self):
      # check params
      self.assertException(TypeError, arizonageneral.make_daemon, 1)
      
      # TODO figure out how to test
      # otherwise tested manually and appears to work as expected





   #------------------------------------------------------------------
   # mutex_lock(program, lockdir="/var/lock")
   #------------------------------------------------------------------
   def test_mutex_lock(self):
      # check params
      self.assertException(TypeError, arizonageneral.mutex_lock, 1)
      self.assertException(TypeError, arizonageneral.mutex_lock, "a", 1)
      self.assertException(TypeError, arizonageneral.mutex_lock, "a", "b", 1)
      
      # create a lock and test for its existence
      os.system("rm /tmp/arizonageneralTest.lock &> /dev/null")
      #Collin: added following line due to the fact that mutex_unlock takes a lock
      lock = arizonageneral.mutex_lock("arizonageneralTest", "/tmp", False)
      self.assertTrue(lock)
      self.assertTrue(os.path.isfile("/tmp/arizonageneralTest.lock"))
      arizonageneral.mutex_unlock(lock)




   
   #------------------------------------------------------------------
   # mutex_unlock()
   #------------------------------------------------------------------
   def test_mutex_unlock(self):
      # create a lock and remove it
      os.system("rm /tmp/arizonageneralTest.lock &> /dev/null")
      #Collin: added following line due to the fact that mutex_unlock takes a lock
      lock = arizonageneral.mutex_lock("arizonageneralTest", "/tmp", False)
      self.assertTrue(lock)
      arizonageneral.mutex_unlock(lock)
      self.assertFalse(os.path.isfile("/tmp/arizonageneralTest"))

   
   
   
   
   #------------------------------------------------------------------
   # Exception_Data(Exception)
   #------------------------------------------------------------------
   def test_Exception_Data(self):
      test = arizonageneral.Exception_Data("test", "test2")
      self.assertEqual(test.message, "test")
      self.assertEqual(test.data, "test2")





   #------------------------------------------------------------------
   # list_to_args(raw_list)
   #------------------------------------------------------------------
   def test_list_to_args(self):
      # check params
      self.assertException(TypeError, arizonageneral.list_to_args, None)
      self.assertException(TypeError, arizonageneral.list_to_args, 1)
 
      self.assertEqual(arizonageneral.list_to_args([]), "")
      self.assertEqual(arizonageneral.list_to_args([""]), " ")
      self.assertEqual(arizonageneral.list_to_args(["a", "b", "c"]), " a b c")
      self.assertEqual(arizonageneral.list_to_args(["a", "(b)", "c"]), " a \\(b\\) c")



   #------------------------------------------------------------------
   # gethostname()
   #------------------------------------------------------------------
   def test_gethostname(self):
      self.assertEqual(arizonageneral.gethostname(),os.getenv("HOSTNAME", None))
      
      
      
      
   #------------------------------------------------------------------
   # getslicename()
   #------------------------------------------------------------------
   def test_getslicename(self):
      self.assertEqual(arizonageneral.getslicename(),None)
      
      
      
      
   #------------------------------------------------------------------
   # getusername()
   #------------------------------------------------------------------
   def test_getusername(self):
      self.assertEquals(arizonageneral.getusername(),os.environ.get("USER"))   
      
      
      
      
   #------------------------------------------------------------------
   # uniq_string(s)
   #------------------------------------------------------------------
   def test_uniq_string(self):
      testString = "this is a test\n of the\n emergency broadcasting system\n this is a test\n this is a test\n this is a test"      
      self.assertEquals(arizonageneral.uniq_string(testString),"this is a test\n of the\n emergency broadcasting system\n this is a test\nprevious line repeated 3 times")
      testString = ""
      self.assertEquals(arizonageneral.uniq_string(testString),"")
      testString = "n\nn\nn\nn\nn\nn\nn\nn\nn\nn\nn\nn\nn\nn\nn\n"
      self.assertEquals(arizonageneral.uniq_string(testString),"n\nprevious line repeated 14 times\n")
      
      
      
      
   #------------------------------------------------------------------
   # error_report(exc_info, program, email=None, files=[], listdirs=[], 
   #              savedir="/tmp", 
   #              title="AUTOMATICALLY GENERATED ERROR REPORT")
   #              -> (mailed, saved, report)
   #------------------------------------------------------------------
   def test_error_report(self):
      # TODO figure out how to test
      pass
      




   #------------------------------------------------------------------
   # valid_fn(filename)
   #------------------------------------------------------------------
   def test_valid_fn(self):

      # A file that should exist and be readable
      self.assertEqual(arizonageneral.valid_fn("/bin/ls"),True)

      # A non-string
      self.assertEqual(arizonageneral.valid_fn(3),False)

      # An invalid path
      self.assertEqual(arizonageneral.valid_fn("/jasdfljk/ajsdfjkadf/asjdf"),False)

      # An invalid file
      self.assertEqual(arizonageneral.valid_fn("/usr/bin/asjdf"),False)

      # A non-file
      self.assertEqual(arizonageneral.valid_fn("/usr/bin"),False)

      # I'd like to test a non-readable file but root can read anything...
# Skip for now
      #self.assertEqual(arizonageneral.valid_fn("/usr/bin"),False)





   #------------------------------------------------------------------
   # text_replace_files_in_fnlist(find, replace, fn_list):
   #------------------------------------------------------------------
   def test_text_replace_files_in_fnlist(self):

      # Set up some files to play with...
      file1orig =  "/tmp/file1"
      file2orig =  "/tmp/file2"
      file3orig =  "/tmp/file3"
      file1 =  "/tmp/file1.scratch"
      file2 =  "/tmp/file2.scratch"
      file3 =  "/tmp/file3.scratch"
 
      # Create the files
      os.system("echo aaa > "+file1orig)
      os.system("echo bbb > "+file2orig)
      os.system("echo aaabb > "+file3orig)

      # Work with clean files
      shutil.copy(file1orig, file1)
      shutil.copy(file2orig, file2)
      shutil.copy(file3orig, file3)



      # Replace the contents of file3
      self.assertEqual(arizonageneral.text_replace_files_in_fnlist("aaabb","?",[file1, file2, file3]),(True,[]))
      self.assertEqual(0, os.system("diff "+file1+" "+file1orig+" > /dev/null"))
      self.assertEqual(0, os.system("diff "+file2+" "+file2orig+" > /dev/null"))
      self.assertEqual(256, os.system("diff "+file3+" "+file3orig+" > /dev/null"))

      # Work with clean files
      shutil.copy(file1orig, file1)
      shutil.copy(file2orig, file2)
      shutil.copy(file3orig, file3)



      # Try to replace something that doesn't exist (okay)
      self.assertEqual(arizonageneral.text_replace_files_in_fnlist("ccc","?",[file1, file2, file3]),(True,[]))
      self.assertEqual(0, os.system("diff "+file1+" "+file1orig+" > /dev/null"))
      self.assertEqual(0, os.system("diff "+file2+" "+file2orig+" > /dev/null"))
      self.assertEqual(0, os.system("diff "+file3+" "+file3orig+" > /dev/null"))

      # Work with clean files
      shutil.copy(file1orig, file1)
      shutil.copy(file2orig, file2)
      shutil.copy(file3orig, file3)
      


      # Replace something in multiple files
      self.assertEqual(arizonageneral.text_replace_files_in_fnlist("a","j",[file1, file2, file3]),(True,[]))
      self.assertEqual(256, os.system("diff "+file1+" "+file1orig+" > /dev/null"))
      self.assertEqual(0, os.system("diff "+file2+" "+file2orig+" > /dev/null"))
      self.assertEqual(256, os.system("diff "+file3+" "+file3orig+" > /dev/null"))

      # Work with clean files
      shutil.copy(file1orig, file1)
      shutil.copy(file2orig, file2)
      shutil.copy(file3orig, file3)
      


      # Try to change an item that doesn't exist (no files should change)
      self.assertEqual(arizonageneral.text_replace_files_in_fnlist("a","j",[file1, file2, file3, "/tmp/adsfas"]),(False, ["/tmp/adsfas"]))
      self.assertEqual(0, os.system("diff "+file1+" "+file1orig+" > /dev/null"))
      self.assertEqual(0, os.system("diff "+file2+" "+file2orig+" > /dev/null"))
      self.assertEqual(0, os.system("diff "+file3+" "+file3orig+" > /dev/null"))


      os.remove(file1)
      os.remove(file2)
      os.remove(file3)
      os.remove(file1orig)
      os.remove(file2orig)
      os.remove(file3orig)
      
      
      
   #------------------------------------------------------------------      
   # text_replace_files_in_fnlist_re(find, replace, fn_list)
   #------------------------------------------------------------------
   def test_text_replace_files_in_fnlist_re(self):
      pass #There's absolutely no difference between this function and the previous one




   #------------------------------------------------------------------
   # remote_popen(hostname, command) -> (out_list, err_list)
   #------------------------------------------------------------------
   def test_remote_popen(self):
      # TODO tests
      pass
      
      
      
   #------------------------------------------------------------------      
   # stream_to_sl(in_stream)
   #------------------------------------------------------------------
   def test_stream_to_sl(self):
      self.assertException(TypeError,arizonageneral.stream_to_sl,"This is not a stream")
      self.assertException(TypeError,arizonageneral.stream_to_sl,('n','e','i','t','h','e','r','i','s','t','h','i','s'))
      self.assertException(TypeError,arizonageneral.stream_to_sl,['n','e','i','t','h','e','r','i','s','t','h','i','s'])
      
      tempf = file("test_stream_to_sl","w")
      tempf.write("Testing this \nstream to sl\ntest one two three")
      tempf.close()
      tempf = file("test_stream_to_sl","r")
      
      self.assertEqual(arizonageneral.stream_to_sl(tempf),["Testing this ","stream to sl","test one two three"])
      tempf.close()
      os.remove("test_stream_to_sl")
      
      
   #------------------------------------------------------------------      
   # get_main_module_path()
   #------------------------------------------------------------------
   def test_get_main_module_path(self):
      self.assertEquals(arizonageneral.get_main_module_path(),os.path.realpath(""))
      
      
      
      
   #------------------------------------------------------------------
   # rmdir_recursive(path)
   #------------------------------------------------------------------
   def test_rmdir_recursive(self):
      #Needs to create directories and test files to remove and check if it was successful
      pass
      
      
      
   #------------------------------------------------------------------      
   # grep_escape(s, special_star=False)
   #------------------------------------------------------------------
   def test_grep_escape(self):
      self.assertEqual(arizonageneral.grep_escape("t[e]s^t<i>ng;"),'t\\\\[e\\\\]s\\\\^t\\<i\\>ng\\;')
      
      
      
     
   #------------------------------------------------------------------   
   # program_exists(name)
   #------------------------------------------------------------------
   def test_program_exists(self):
      pass
      
      
      
      
      
   
# Run tests
if __name__=='__main__':
   arizonaunittest.main()
