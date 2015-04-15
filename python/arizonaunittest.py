#! /usr/bin/env python
"""
<Program Name>
   arizonaunittest.py

<Started>   
   May 18, 2005

<Author>
   Programmed by Jeffry Johnston under the direction of Justin Cappos.

   Extended by Mario Gonzalez.

<Purpose>
   Unit testing framework, based on the unittest module.  Defines new 
   functions to aid in unit testing.
"""

# imports
import os
import sys
import unittest
from StringIO import StringIO





class TestCase(unittest.TestCase): 
   """
   <Purpose>
      Extends unittest.TestCase with additional functionality
   <Parent>
      unittest.TestCase
   """





   # internal helper functions
   def setUp(self):
      self.redirect_stdout()
      self.redirect_stderr()

   def tearDown(self):
      self.restore_stdout()  
      self.restore_stderr()  
      
      
      
      
      
   def set_cmdline(self, arg_list):
      """
      <Purpose>
         Sets the command line arguments for the program being tested.
         
      <Arguments>    
         arg_list: 
                 List of command line arguments
   
      <Exceptions>
         None.
   
      <Side Effects>
         Changes sys.argv[1:]

      <Returns>
         None.
      """
      sys.argv[1:] = arg_list   
      




   def debug_print(self, text):
      """
      <Purpose>
         Prints the given string of text to the standard output in a way 
         that it will not be captured by the stdout redirector.
         
      <Arguments>    
         text: 
                 Text to print to stdout
   
      <Exceptions>
         None.
   
      <Side Effects>
         None.

      <Returns>
         None.
      """
      os.system('echo "' + str(text) + '"') 





   def redirect_stdout(self):
      """
      <Purpose>
         Redirects stdout to be captured to an internal buffer.
         
      <Arguments>    
         None.
   
      <Exceptions>
         None.
   
      <Side Effects>
         Changes stdout_old, stdout_redirect, sys.stdout 

      <Returns>
         None.
      """
      self.stdout_old = sys.stdout
      self.stdout_redirect = StringIO()
      sys.stdout = self.stdout_redirect
      




   def redirect_stderr(self):
      """
      <Purpose>
         Redirects stderr to be captured to an internal buffer.
         
      <Arguments>    
         None.
   
      <Exceptions>
         None.
   
      <Side Effects>
         Changes stderr_old, stderr_redirect, sys.stderr 

      <Returns>
         None.
      """
      self.stderr_old = sys.stderr
      self.stderr_redirect = StringIO()
      sys.stderr = self.stderr_redirect





   def restore_stdout(self):
      """
      <Purpose>
         Restores stdout so that output is no longer captured.
         
      <Arguments>    
         None.
   
      <Exceptions>
         None.
   
      <Side Effects>
         Changes sys.stdout 

      <Returns>
         None.
      """
      sys.stdout = self.stdout_old 





   def restore_stderr(self):
      """
      <Purpose>
         Restores stderr so that output is no longer captured.
         
      <Arguments>    
         None.
   
      <Exceptions>
         None.
   
      <Side Effects>
         Changes sys.stderr 

      <Returns>
         None.
      """
      sys.stderr = self.stderr_old 
   




   def stdout(self):   
      """
      <Purpose>
         Returns the current standard output buffer as a string.
         
      <Arguments>    
         None.
   
      <Exceptions>
         None.
   
      <Side Effects>
         None. 

      <Returns>
         The current standard output buffer as a string.
      """
      self.stdout_redirect.seek(0)
      return self.stdout_redirect.read()





   def stderr(self):   
      """
      <Purpose>
         Returns the current standard error buffer as a string.
         
      <Arguments>    
         None.
   
      <Exceptions>
         None.
   
      <Side Effects>
         None. 

      <Returns>
         The current standard error buffer as a string.
      """
      self.stderr_redirect.seek(0)
      return self.stderr_redirect.read()
      




   def reset_stdout(self):
      """
      <Purpose>
         Resets (clears) the stored standard output buffer.
         
      <Arguments>    
         None.
   
      <Exceptions>
         None.
   
      <Side Effects>
         None. 

      <Returns>
         None.
      """
      self.stdout_redirect.truncate(0) 





   def reset_stderr(self):
      """
      <Purpose>
         Resets (clears) the stored standard error buffer.
         
      <Arguments>    
         None.
   
      <Exceptions>
         None.
   
      <Side Effects>
         None. 

      <Returns>
         None.
      """
      self.stderr_redirect.truncate(0) 





   def assertStdout(self, output):
      """
      <Purpose>
         Tests that the collected stdout matches the specified string.
        
      <Arguments>    
         output: 
                 Expected output string.
   
      <Exceptions>
         AssertionError if test doesn't pass.
   
      <Side Effects>
         None. 

      <Returns>
         None.
      """
      self.failUnlessEqual(self.stdout(), output)   





   def assertStderr(self, output):
      """
      <Purpose>
         Tests that the collected stderr matches the specified string.
        
      <Arguments>    
         output: 
                 Expected output string.
   
      <Exceptions>
         AssertionError if test doesn't pass.
   
      <Side Effects>
         None. 

      <Returns>
         None.
      """
      self.failUnlessEqual(self.stderr(), output)   





   def assertException(self, exception, function, *args):
      """
      <Purpose>
         Tests that the specified exception was thrown.  Similar to 
         assertRaises, but also works with SystemExit.
        
      <Arguments>    
         exception: 
                 Desired exception.
         function: 
                 Function name (including module if necessary).
         *args: 
                 Optional arguments to the function, comma separated.  Not
                 a tuple.  List the arguments as they would appear to the 
                 function if called directly.  Keywords are not supported. 
   
      <Exceptions>
         AssertionError if test doesn't pass.
   
      <Side Effects>
         None. 

      <Returns>
         None.
      """
      try:
         function(*args)
      except exception:
         pass
      else:
         self.fail() 
      


   def assertExceptionMessage(self, exception, message, function, *args):
      """
      <Purpose>
         This is an extension of assertException: it contains the behavior of assertException
         and it also asserts that the exception thrown contains
         the message specified.
         
      <Arguments>
         exception:
               Desired exception.

         message:
               Desired message as a string.

         function:
               Function name (including module if necessary).

         *args:
               Optional arguments to the function, comma separated.  Not
               a tuple.  List the arguments as they would appear to the
               function if called directly.  Keywords are not supported.
                                                   
      <Exceptions>
         AssertionError if test doesn't pass.

      <Output>
         If the exception fails, then a message contains the exception actually thrown.
         If the message fails, then a message contains the actual exception message.

      <Side Effects>
         None.

      <Returns>
         None.
      """
      
      try:
         function(*args)
      except Exception, e:
         if exception != sys.exc_info()[0]:
            self.fail("Exception Failure - The actual exception thrown was: " + str(sys.exc_info()[0]))
         else:
            try:
               if e.message != message:
                  self.fail("Exception Message Failure - The exception thrown contained this message: " + e.message)
            except AttributeError, err:   # the exception is a built-in type with no "message" attribute.
               if e.__str__() != message:
                  self.fail("Exception Message Failure - The exception thrown contained this message: " + e.__str__())



   def assertNoException(self, function, *args):
      """
      <Purpose>
         Used when the given function should not raise any exception.
         Fails if the given function raises an exception and prints its message.
         This is a convenience test.

      <Arguments>
         function:
            Function name (including module if necessary).

         *args:
            Optional arguments to the function, comma separated.  Not
            a tuple.  List the arguments as they would appear to the
            function if called directly.  Keywords are not supported.

      <Exceptions>
         AssertionError if test doesn't pass.

      <Output>
         If the function raises an exception, then this test fails and prints the message contained in that exception.

      <Side Effects>
         None.

      <Returns>
         None.
      """
      
      try:
         function(*args)
      except Exception, e:
         try:
            # try printing the user-defined exception's message
            self.fail( e.message )
         except AttributeError, err:
            # the exception was not a user-defined, it was built-in. Print its message
            self.fail( e.__str__() )

         

   def assertTrue(self, condition):
      """
      <Purpose>
         Tests that condition is true.
        
      <Arguments>    
         condition: 
                 Expression/function to test.
   
      <Exceptions>
         AssertionError if test doesn't pass.
   
      <Side Effects>
         None. 

      <Returns>
         None.
      """
      self.failIf(not condition)
      




   def assertFalse(self, condition):     
      """
      <Purpose>
         Tests that condition is false.
        
      <Arguments>    
         condition: 
                 Expression/function to test.
   
      <Exceptions>
         AssertionError if test doesn't pass.
   
      <Side Effects>
         None. 

      <Returns>
         None.
      """
      self.failIf(condition)




      
   #------------------------------------------------------------------
   # assertEqual(first, second):
   #  
   # <Purpose>
   #    Tests that first == second.
   #
   # <Arguments>
   #    first: 
   #            Desired result.
   #    second: 
   #            Expression/function to test.
   #------------------------------------------------------------------

   #------------------------------------------------------------------
   # assertNotEqual(first, second):
   #  
   # <Purpose>
   #    Tests that first != second.
   #
   # <Arguments>
   #    first: 
   #            Unwanted result.
   #    second: 
   #            Expression/function to test.
   #------------------------------------------------------------------
   
   #------------------------------------------------------------------
   # fail():
   #  
   # <Purpose>
   #    Causes the test to fail if executed.
   #
   # <Arguments>
   #    None.
   #------------------------------------------------------------------

   #------------------------------------------------------------------
   # failIf(condition):
   #  
   # <Purpose>
   #    Causes the test to fail if condition is true.
   #
   # <Arguments>
   #    condition:
   #            Expression/function to test
   #------------------------------------------------------------------
   




# Run tests
def main(verbose=None):
   if not verbose:unittest.main()   
   else:
      unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
